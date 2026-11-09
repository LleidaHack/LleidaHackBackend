"""Organizer-reviewed CSV imports. Never fetch user-provided project URLs."""

import csv
import hashlib
import io
import json
from collections import Counter
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, Field

from src.impl.HackerGroup.model import HackerGroup
from src.impl.Operations import service as ops
from src.impl.Operations.model import DevpostProject, OperationAudit, Presentation
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(tags=["Event Operations"])
MAX_ROWS = 2000
ALIASES = {
    "url": ["project url", "submission url", "devpost url", "url"],
    "title": ["project title", "project name", "title"],
    "description": ["description", "project description", "descripció"],
    "repository_url": ["repository", "repository url", "github"],
    "demo_url": ["demo", "demo url", "video"],
    "team": [
        "hackeps team code",
        "codi d’equip",
        "codi d'equip",
        "código de equipo",
        "team code",
    ],
    "challenge": ["challenge", "repte", "reto"],
    "mlh": ["mlh", "participate in mlh"],
    "status": ["submission status", "status", "project status"],
}


class ImportInput(BaseModel):
    csv_text: str = Field(min_length=1, max_length=1_000_000)
    columns: dict[str, str] = Field(default_factory=dict, max_length=9)
    challenges: dict[str, str] = Field(default_factory=dict, max_length=100)
    completed_statuses: list[str] = Field(
        default_factory=lambda: ["submitted", "complete", "completed"], max_length=30
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
        rows = []
        for values in reader:
            if not any(v.strip() for v in values):
                continue
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
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() not in {"devpost.com", "www.devpost.com"}
        or len(parts) != 2
        or parts[0] != "software"
        or not parts[1]
        or len(value) > 500
    ):
        raise ValueError("Expected an https://devpost.com/software/... project URL")
    return "https://devpost.com/software/" + parts[1]


def preview(event_id, body, state):
    headers, source = read_csv(body)
    columns = {
        key: body.columns.get(
            key, next((h for h in headers if h.casefold() in aliases), "")
        )
        for key, aliases in ALIASES.items()
    }
    errors = []
    for key in ("url", "title", "team", "challenge"):
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
        g.code: g for g in db.session.query(HackerGroup).filter_by(event_id=event_id)
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
        if c.get("published") and c["id"] in rooms and c["id"] != "mlh"
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
        if len(item["description"]) > 10000:
            item["errors"].append("Project description exceeds 10000 characters")
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
        group = groups.get(get("team"))
        if not group:
            item["errors"].append("Team code does not belong to this event")
        else:
            item.update(group_id=group.id, team=group.name)
        chosen = body.challenges.get(get("challenge"), get("challenge"))
        matches = [
            c
            for c in challenges
            if chosen == c["id"] or chosen.casefold() == c["title"].casefold()
        ]
        if len(matches) != 1:
            item["errors"].append(
                "Map this challenge to one published challenge with a room"
            )
        else:
            item["challenge"] = matches[0]["id"]
        mlh = get("mlh").casefold()
        if mlh not in {"", "yes", "true", "1", "sí", "si", "no", "false", "0"}:
            item["errors"].append("MLH must be yes/no, true/false, or 1/0")
        item["mlh"] = mlh in {"yes", "true", "1", "sí", "si"}
        if item["mlh"] and "mlh" not in rooms:
            item["errors"].append("Configure the MLH room first")
        linked = by_url.get(item.get("url"))
        if linked and group and linked.group_id != group.id:
            item["errors"].append("Project is already linked to a different team")
        if group and group.id in by_team and by_team[group.id].url != item.get("url"):
            item["errors"].append("Team is already linked to another project")
        if group:
            team_turns = [p for p in turns if p.group_id == group.id]
            item["queue_action"] = "preserve" if team_turns else "create"
            if team_turns:
                item["warnings"].append(
                    "Existing turns and manual adjustments will be preserved"
                )
                wanted = {item.get("challenge")} | ({"mlh"} if item["mlh"] else set())
                if {p.track for p in team_turns} != wanted:
                    item["warnings"].append(
                        "Imported challenge/MLH differs from the queue; review the team manually"
                    )
        item["action"] = "update" if linked else "create"
        rows.append(item)
    eligible = [r for r in rows if r["action"] != "skip"]
    urls = Counter(r.get("url") for r in eligible if r.get("url"))
    teams = Counter(r.get("group_id") for r in eligible if r.get("group_id"))
    for item in eligible:
        if urls[item.get("url")] > 1 or teams[item.get("group_id")] > 1:
            item["errors"].append("Duplicate project or team in this CSV")
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
    result["digest"] = digest(
        {
            "input": body.model_dump(include=set(ImportInput.model_fields)),
            "preview": result,
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
        for key in ("title", "challenge", "mlh"):
            setattr(project, key, item[key])
        for key in ("description", "repository_url", "demo_url"):
            if plan["columns"].get(key):
                setattr(project, key, item[key])
        if item["queue_action"] == "create":
            for track in [item["challenge"]] + (["mlh"] if item["mlh"] else []):
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
