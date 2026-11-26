"""Organizer-reviewed CSV imports. Never fetch user-provided project URLs."""

import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, Field

from src.impl.HackerGroup.model import HackerGroup
from src.impl.Operations import ribo
from src.impl.Operations import service as ops
from src.impl.Operations.model import (
    ChallengeVote,
    DevpostProject,
    OperationAudit,
    Presentation,
)
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(tags=["Event Operations"])
MAX_ROWS = 2000
ALIASES = {
    "url": ["project url", "submission url", "devpost url", "url"],
    "title": ["project title", "project name", "title"],
    "description": [
        "description",
        "project description",
        "descripció",
        "about the project",
    ],
    "repository_url": ["repository", "repository url", "github"],
    "demo_url": ["demo", "demo url", "video", "video demo link"],
    "try_links": ['"try it out" links', "try it out links"],
    "gallery": ["image gallery urls"],
    "technologies": ["built with"],
    "team": [
        "hackeps team code",
        "codi d’equip",
        "codi d'equip",
        "código de equipo",
        "team code",
        "teamid",
        "team id",
    ],
    "challenge": ["challenge", "repte", "reto"],
    "mlh": ["mlh", "participate in mlh"],
    "status": ["submission status", "status", "project status"],
}


CHALLENGE_MAPPING_ERROR = "Map this challenge to one published challenge with a room"


class ImportInput(BaseModel):
    csv_text: str = Field(min_length=1, max_length=1_000_000)
    columns: dict[str, str] = Field(default_factory=dict, max_length=len(ALIASES))
    challenges: dict[str, str] = Field(default_factory=dict, max_length=100)
    completed_statuses: list[str] = Field(
        default_factory=lambda: [
            "submitted",
            "complete",
            "completed",
            "submitted (gallery/visible)",
        ],
        max_length=30,
    )
    completed_only: bool = False
    filename: str = Field(default="projects.csv", max_length=200)


class ImportCommit(ImportInput):
    preview_digest: str = Field(min_length=64, max_length=64)
    operation_id: UUID
    reason: str = Field(min_length=3, max_length=500)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def read_csv(body):
    text = body.csv_text.lstrip("\ufeff")
    if "\x00" in text:
        raise HTTPException(422, "CSV contains null bytes")
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    try:
        reader = csv.reader(io.StringIO(text, newline=""), dialect, strict=True)
        headers = [h.strip() for h in next(reader)]
        if (
            not headers
            or len(headers) > 150
            or any(not h or len(h) > 500 for h in headers)
            or len(set(headers)) != len(headers)
        ):
            raise HTTPException(
                422, "CSV headers must be unique, non-empty, and bounded"
            )
        # Devpost represents a variable number of member triples with one example and an ellipsis.
        member_headers = [
            "Additional Team Member Count",
            "Team Member 1 First Name",
            "Team Member 1 Last Name",
            "Team Member 1 Email",
            "...",
        ]
        member_index = (
            headers.index(member_headers[0]) if member_headers[0] in headers else -1
        )
        variable_members = (
            member_index >= 0
            and headers[member_index : member_index + 5] == member_headers
        )
        if variable_members:
            headers = headers[: member_index + 1] + headers[member_index + 5 :]
        rows = []
        for values in reader:
            if not any(v.strip() for v in values):
                continue
            if variable_members and len(values) > member_index:
                count = values[member_index].strip()
                if re.fullmatch(r"[0-9]{1,4}", count) and len(values) == len(
                    headers
                ) + 3 * int(count):
                    values = (
                        values[: member_index + 1]
                        + values[member_index + 1 + 3 * int(count) :]
                    )
                else:
                    raise HTTPException(
                        422, f"CSV row {len(rows) + 2} has invalid team member columns"
                    )
            if len(values) != len(headers):
                raise HTTPException(
                    422, f"CSV row {len(rows) + 2} has the wrong number of columns"
                )
            rows.append(dict(zip(headers, (v.strip() for v in values))))
            if len(rows) > MAX_ROWS:
                raise HTTPException(422, "CSV exceeds 2000 projects")
        return headers, rows
    except (csv.Error, StopIteration) as exc:
        raise HTTPException(422, "Invalid or empty CSV") from exc


def project_url(value):
    parsed = urlsplit(value)
    parts = parsed.path.strip("/").split("/")
    host = parsed.netloc.lower()
    if parsed.scheme == "https" and len(value) <= 500 and len(parts) == 2 and parts[1]:
        if host in {"devpost.com", "www.devpost.com"} and parts[0] == "software":
            return "https://devpost.com/software/" + parts[1]
        if (
            re.fullmatch(r"[a-z0-9-]+\.devpost\.com", host)
            and parts[0] == "submissions"
            and re.fullmatch(r"[0-9]+(?:-[^/?#\s]+)?", parts[1])
        ):
            return f"https://{host}/submissions/{parts[1]}"
    raise ValueError("Expected a Devpost project or submission URL")


def preview(event_id, body, state):
    headers, source = read_csv(body)
    columns = {
        key: body.columns.get(
            key, next((h for h in headers if h.casefold() in aliases), "")
        )
        for key, aliases in ALIASES.items()
    }
    errors = []
    for key in ("url", "title"):
        if columns[key] not in headers:
            errors.append(f"Select the {key} column")
    if not body.completed_only and columns["status"] not in headers:
        errors.append("Select the status column or confirm this export excludes drafts")
    if any(v and v not in headers for v in columns.values()):
        errors.append("A mapped column is missing from the CSV")
    selected = [v for v in columns.values() if v]
    if len(selected) != len(set(selected)):
        errors.append("Map each field to a different CSV column")
    if not body.completed_only and not any(s.strip() for s in body.completed_statuses):
        errors.append("Select at least one completed submission status")
    groups = {
        g.id: g for g in db.session.query(HackerGroup).filter_by(event_id=event_id)
    }
    groups_by_code = defaultdict(list)
    for g in groups.values():
        groups_by_code[g.code.strip().removeprefix("#").strip()].append(g)
    choices = {
        v.group_id: v
        for v in db.session.query(ChallengeVote).filter_by(event_id=event_id)
    }
    existing = list(db.session.query(DevpostProject).filter_by(event_id=event_id))
    by_url = {p.url: p for p in existing}
    by_team = {p.group_id: p for p in existing}
    turns = list(
        db.session.query(Presentation)
        .filter_by(event_id=event_id)
        .order_by(Presentation.id)
    )
    rooms = {r["id"] for r in state.config.get("rooms", [])}
    challenges = [
        c
        for c in state.config.get("challenges", [])
        if c.get("published")
        and c["id"] in rooms
        and c["id"] not in {"mlh", ribo.ROOM_ID}
    ]
    rows = []
    for index, source_row in enumerate(source, 2):

        def get(key, values=source_row):
            return values.get(columns[key], "")

        item = {
            "row": index,
            "title": get("title")[:150],
            "team_code": get("team")[:100],
            "status": get("status")[:100],
            "challenge_value": get("challenge")[:150],
            "errors": [],
            "warnings": [],
            "action": "skip",
        }
        if errors:
            rows.append(item)
            continue
        if not body.completed_only and get("status").casefold() not in {
            s.strip().casefold() for s in body.completed_statuses
        }:
            item["warnings"].append("Not a selected completed status; excluded")
            rows.append(item)
            continue
        item["action"] = "import"
        try:
            item["url"] = project_url(get("url"))
        except ValueError as exc:
            item["errors"].append(str(exc))
        if not get("title") or len(get("title")) > 150:
            item["errors"].append("Project title must contain 1–150 characters")
        item["description"] = get("description")
        for field in ("repository_url", "demo_url"):
            value = get(field)
            try:
                parsed = urlsplit(value)
                if value and (
                    len(value) > 500
                    or parsed.scheme not in {"http", "https"}
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                ):
                    raise ValueError("Invalid link")
            except ValueError:
                item["errors"].append(
                    "Project links must be HTTP or HTTPS URLs without credentials"
                )
            item[field] = value
        materials = {}
        if columns["technologies"]:
            materials["technologies"] = get("technologies")
        for field in ("try_links", "gallery"):
            if not columns[field]:
                continue
            links = []
            for link in filter(
                None,
                re.split(r",\s*(?=https?://)|[\r\n]+", get(field), flags=re.IGNORECASE),
            ):
                link = link.strip()
                try:
                    parsed = urlsplit(link)
                    if (
                        parsed.scheme not in {"http", "https"}
                        or not parsed.hostname
                        or parsed.username
                        or parsed.password
                        or any(c.isspace() for c in link)
                    ):
                        raise ValueError
                except ValueError:
                    item["errors"].append(
                        "Project links must be HTTP or HTTPS URLs without credentials"
                    )
                    break
                if link not in links:
                    links.append(link)
            materials[field] = links
        item["materials"] = materials
        code = get("team").strip().removeprefix("#").strip()
        candidates = groups_by_code.get(code, []) if code else []
        group = candidates[0] if len(candidates) == 1 else None
        linked = by_url.get(item.get("url"))
        if linked and linked.group_id:
            if group and group.id != linked.group_id:
                item["errors"].append("Project is already linked to a different team")
            group = groups.get(linked.group_id)
        if group and group.id in by_team and by_team[group.id].url != item.get("url"):
            group = None
        item.update(
            group_id=None, challenge="", queue_action="pending", add_ribo_turn=False
        )
        if group:
            item.update(group_id=group.id, team=group.name)
        chosen = body.challenges.get(get("challenge"), get("challenge"))
        if not columns["challenge"] and group and group.id in choices:
            chosen = choices[group.id].challenge
        matches = [
            c
            for c in challenges
            if chosen == c["id"] or chosen.casefold() == c["title"].casefold()
        ]
        if len(matches) == 1:
            item["challenge"] = matches[0]["id"]
        elif group:
            item["errors"].append(CHALLENGE_MAPPING_ERROR)
        mlh = get("mlh").casefold()
        if mlh not in {"", "yes", "true", "1", "sí", "si", "no", "false", "0"}:
            item["errors"].append("MLH must be yes/no, true/false, or 1/0")
        item["mlh"] = mlh in {"yes", "true", "1", "sí", "si"}
        if item["mlh"] and "mlh" not in rooms:
            item["errors"].append("Configure the MLH room first")
        if group:
            team_turns = [p for p in turns if p.group_id == group.id]
            item["queue_action"] = "preserve" if team_turns else "create"
            vote = choices.get(group.id)
            item["ribo_prize"] = bool(vote and vote.ribo_prize)
            item["add_ribo_turn"] = item["ribo_prize"] and not any(
                p.track == ribo.ROOM_ID for p in team_turns
            )
            if team_turns:
                item["warnings"].append(
                    "Existing turns and manual adjustments will be preserved"
                )
                wanted = {item.get("challenge")} | ({"mlh"} if item["mlh"] else set())
                if {p.track for p in team_turns if p.track != ribo.ROOM_ID} != wanted:
                    item["warnings"].append(
                        "Imported challenge/MLH differs from the queue; review the team manually"
                    )
        item["action"] = ("update" if linked else "create") if group else "pending"
        rows.append(item)
    eligible = [r for r in rows if r["action"] != "skip"]
    urls = Counter(r.get("url") for r in eligible if r.get("url"))
    teams = Counter(r.get("group_id") for r in eligible if r.get("group_id"))
    for item in eligible:
        if urls[item.get("url")] > 1:
            item["errors"].append("Duplicate project or team in this CSV")
        elif teams[item.get("group_id")] > 1 and not getattr(
            by_url.get(item.get("url")), "group_id", None
        ):
            item.update(
                action="pending",
                group_id=None,
                team=None,
                queue_action="pending",
                add_ribo_turn=False,
            )
            if CHALLENGE_MAPPING_ERROR in item["errors"]:
                item["errors"].remove(CHALLENGE_MAPPING_ERROR)
            if not columns["challenge"]:
                item["challenge"] = ""
    if not source:
        errors.append("The CSV has no projects")
    if not eligible and not errors:
        errors.append("No completed submissions match the selected statuses")
    result = {
        "headers": headers,
        "columns": columns,
        "challenge_values": sorted(
            {r["challenge_value"] for r in rows if r["challenge_value"]}
        ),
        "rows": rows,
        "errors": errors,
        "version": state.version,
        "ready": bool(eligible)
        and not errors
        and not any(r["errors"] for r in eligible),
        "count": len(eligible),
    }
    # Includes queue state and existing links to detect edits after preview.
    # The event state version is excluded: unrelated changes (a paused room, a
    # new alert) must not invalidate a preview whose imported content is unchanged.
    result["digest"] = digest(
        {
            "input": body.model_dump(include=set(ImportInput.model_fields)),
            "preview": {k: v for k, v in result.items() if k != "version"},
            "links": sorted(
                (
                    p.url,
                    p.group_id,
                    p.title,
                    p.challenge,
                    p.mlh,
                    p.description,
                    p.repository_url,
                    p.demo_url,
                    p.materials,
                )
                for p in existing
            ),
            "turns": [
                (p.id, p.version, p.room, p.state, p.scheduled_at, p.pinned, p.position)
                for p in turns
            ],
        }
    )
    return result


@router.post("/{event_id}/devpost/preview")
def preview_import(
    event_id: int, body: ImportInput, token: BaseToken = Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, state = ops.state(event_id)
    result = preview(event_id, body, state)
    db.session.commit()
    return result


@router.post("/{event_id}/devpost/import")
def commit_import(
    event_id: int, body: ImportCommit, token: BaseToken = Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, state = ops.state(event_id, True)
    fingerprint = digest(body.model_dump(mode="json"))
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=str(body.operation_id))
        .first()
    )
    if previous:
        if (
            previous.action != "devpost.import"
            or previous.details.get("fingerprint") != fingerprint
            or previous.actor_id != token.user_id
        ):
            raise HTTPException(409, "Import operation ID was already used")
        return previous.result
    plan = preview(event_id, body, state)
    if body.preview_digest != plan["digest"]:
        raise HTTPException(409, "Import preview is stale; preview again")
    if not plan["ready"]:
        raise HTTPException(422, "Resolve all preview errors before importing")
    changes = []
    created_turns = 0
    for item in plan["rows"]:
        if item["action"] == "skip":
            continue
        project = (
            db.session.query(DevpostProject)
            .filter_by(event_id=event_id, url=item["url"])
            .first()
        )
        before = (
            {k: getattr(project, k) for k in ("title", "challenge", "mlh")}
            if project
            else None
        )
        if project is None:
            project = DevpostProject(
                event_id=event_id, group_id=item["group_id"], url=item["url"]
            )
            db.session.add(project)
        project.group_id = item["group_id"]
        project.submitted_team_code = item["team_code"]
        for key in ("title", "challenge", "mlh"):
            setattr(project, key, item[key])
        for key in ("description", "repository_url", "demo_url"):
            if plan["columns"].get(key):
                setattr(project, key, item[key])
        project.materials = {**(project.materials or {}), **item["materials"]}
        tracks = []
        if item["queue_action"] == "create":
            tracks = [item["challenge"]] + (["mlh"] if item["mlh"] else [])
        if item["add_ribo_turn"]:
            ribo.ensure_room(state)
            tracks.append(ribo.ROOM_ID)
        for track in tracks:
            db.session.add(
                Presentation(
                    event_id=event_id,
                    group_id=item["group_id"],
                    room=track,
                    track=track,
                )
            )
            created_turns += 1
        changes.append(
            {
                "url": item["url"],
                "group_id": item["group_id"],
                "before": before,
                "after": {k: item[k] for k in ("title", "challenge", "mlh")},
                "queue_action": item["queue_action"],
                "warnings": item["warnings"],
            }
        )
    state.version += 1
    result = {
        "imported": len(changes),
        "pending": sum(item["action"] == "pending" for item in plan["rows"]),
        "created_turns": created_turns,
        "skipped": len(plan["rows"]) - len(changes),
    }
    log = ops.audit(
        event_id,
        token,
        "devpost.import",
        {
            "filename": body.filename,
            "reason": body.reason,
            "sha256": hashlib.sha256(body.csv_text.encode()).hexdigest(),
            "fingerprint": fingerprint,
            "columns": plan["columns"],
            "completed_only": body.completed_only,
            "completed_statuses": body.completed_statuses,
            "challenges": body.challenges,
            "changes": changes,
        },
        operation_id=str(body.operation_id),
        result=result,
    )
    result = {**result, "audit_id": log.id}
    log.result = result
    db.session.commit()
    return result


@router.get("/{event_id}/devpost/projects")
def imported_projects(event_id: int, token: BaseToken = Depends(JWTBearer())):
    ops.require_organizer(token)
    ops.state(event_id)
    return [
        {
            "id": p.id,
            "submitted_team_code": p.submitted_team_code,
            "url": p.url,
            "title": p.title,
            "group_id": p.group_id,
            "challenge": p.challenge,
            "mlh": p.mlh,
        }
        for p in db.session.query(DevpostProject)
        .filter_by(event_id=event_id)
        .order_by(DevpostProject.id)
    ]


class TeamAssignment(BaseModel):
    group_id: int
    challenge: str | None = Field(default=None, max_length=80)


@router.put("/{event_id}/devpost/projects/{project_id}/team")
def assign_project(
    event_id: int,
    project_id: int,
    body: TeamAssignment,
    token: BaseToken = Depends(JWTBearer()),
):
    ops.require_organizer(token)
    _, state = ops.state(event_id, True)
    project = (
        db.session.query(DevpostProject)
        .filter_by(event_id=event_id, id=project_id)
        .first()
    )
    group = (
        db.session.query(HackerGroup)
        .filter_by(event_id=event_id, id=body.group_id)
        .first()
    )
    if not project or not group:
        raise HTTPException(404, "Project or team not found in this event")
    if project.group_id == group.id:
        return {"ok": True}
    if (
        project.group_id
        or db.session.query(DevpostProject)
        .filter_by(event_id=event_id, group_id=group.id)
        .first()
    ):
        raise HTTPException(409, "Project or team already linked")
    vote = (
        db.session.query(ChallengeVote)
        .filter_by(event_id=event_id, group_id=group.id)
        .first()
    )
    selected = project.challenge if body.challenge is None else body.challenge
    challenge = selected or (vote.challenge if vote else "")
    rooms = {r["id"] for r in state.config.get("rooms", [])}
    published = {
        c["id"] for c in state.config.get("challenges", []) if c.get("published")
    }
    if challenge not in rooms & published or challenge in {"mlh", ribo.ROOM_ID}:
        raise HTTPException(422, "Select a published challenge with a room")
    turns = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id, group_id=group.id)
        .all()
    )
    if not turns:
        if project.mlh and "mlh" not in rooms:
            raise HTTPException(422, "Configure the MLH room first")
        for track in [challenge] + (["mlh"] if project.mlh else []):
            db.session.add(
                Presentation(
                    event_id=event_id, group_id=group.id, room=track, track=track
                )
            )
        db.session.flush()
    if vote and vote.ribo_prize:
        ribo.sync_choice(state, group.id, True)
    project.group_id = group.id
    project.challenge = challenge
    state.version += 1
    ops.audit(
        event_id,
        token,
        "devpost.assign",
        {"project_id": project_id, "group_id": group.id, "challenge": challenge},
    )
    db.session.commit()
    return {"ok": True}
