import csv
import io
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text


@pytest.fixture
def setup_import(client, create_user, create_event, create_group):
    organizer = create_user(role="organizer")
    hacker = create_user()
    event = create_event([hacker])
    group = create_group(event, [hacker])
    base = f"/v1/operations/{event}"
    config = client.get(base + "/manage", headers=organizer.headers).json()
    start = datetime.now(UTC) + timedelta(hours=1)
    config.update(
        challenges=[{"id": "c1", "title": "Challenge", "published": True}],
        rooms=[{"id": "c1", "title": "Room 1"}, {"id": "mlh", "title": "MLH"}],
        judging_start=start.isoformat(),
        judging_end=(start + timedelta(hours=2)).isoformat(),
        phase="hacking",
    )
    response = client.put(
        base + "/config",
        headers=organizer.headers,
        json={
            "version": config["version"],
            "config": config,
            "reason": "Prepare import",
        },
    )
    assert response.status_code == 200, response.text
    return organizer, hacker, event, group, base


def payload(code, **overrides):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(
        [
            "Project URL",
            "Project Title",
            "HackEPS Team Code",
            "Challenge",
            "MLH",
            "Status",
        ]
    )
    writer.writerow(
        [
            "https://devpost.com/software/tractor",
            "Tractor, smart farming",
            code,
            "Challenge",
            "Yes",
            "Submitted",
        ]
    )
    writer.writerow(
        [
            "https://devpost.com/software/draft",
            "Draft",
            "unknown",
            "other",
            "No",
            "Draft",
        ]
    )
    return {"csv_text": "\ufeff" + stream.getvalue(), **overrides}


def commit(client, organizer, base, body):
    preview = client.post(
        base + "/devpost/preview", headers=organizer.headers, json=body
    )
    assert preview.status_code == 200, preview.text
    plan = preview.json()
    data = {
        **body,
        "preview_digest": plan["digest"],
        "operation_id": str(uuid4()),
        "reason": "Final submitted projects",
    }
    return (
        client.post(base + "/devpost/import", headers=organizer.headers, json=data),
        data,
        plan,
    )


def test_import_preview_replay_reimport_and_audit(client, setup_import, engine):
    o, h, event, group, base = setup_import
    body = payload(group.code)
    response, data, plan = commit(client, o, base, body)
    assert plan["ready"] and plan["count"] == 1
    assert plan["rows"][1]["action"] == "skip"
    assert response.status_code == 200, response.text
    assert response.json()["created_turns"] == 2
    assert (
        client.post(base + "/devpost/import", headers=o.headers, json=data).json()
        == response.json()
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE event_presentation SET pinned=1, state='called', version=3 WHERE event_id=:event"
            ),
            {"event": event},
        )
    response, _, plan = commit(client, o, base, body)
    assert response.status_code == 200, response.text
    assert response.json()["created_turns"] == 0
    assert plan["rows"][0]["queue_action"] == "preserve"
    turns = client.get(base + "/manage", headers=o.headers).json()["presentations"]
    assert len(turns) == 2 and all(
        t["state"] == "called" and t["pinned"] == 1 and t["version"] == 3 for t in turns
    )
    logs = client.get(base + "/audit?action=devpost.import", headers=o.headers).json()
    assert len(logs) == 2
    assert logs[0]["details"]["reason"] == "Final submitted projects"
    assert client.get(base + "/devpost/projects", headers=h.headers).status_code == 403
    assert (
        client.post(base + "/devpost/preview", headers=h.headers, json=body).status_code
        == 403
    )
    assert (
        client.post(base + "/devpost/import", headers=h.headers, json=data).status_code
        == 403
    )
    projects = client.get(base + "/devpost/projects", headers=o.headers).json()
    assert len(projects) == 1 and projects[0]["group_id"] == group.id


@pytest.mark.parametrize(
    "change",
    ["duplicate", "unknown", "challenge", "url", "mlh", "status", "missing_status"],
)
def test_invalid_rows_block_atomic_import(client, setup_import, change):
    o, _, _, group, base = setup_import
    body = payload(group.code)
    if change == "duplicate":
        body["csv_text"] += body["csv_text"].splitlines()[1] + "\n"
    elif change == "unknown":
        body = payload("foreign-team")
    elif change == "challenge":
        body["challenges"] = {"Challenge": "unconfigured"}
    elif change == "url":
        body["csv_text"] = body["csv_text"].replace(
            "https://devpost.com/software/tractor", "javascript:alert(1)"
        )
    elif change == "mlh":
        body["csv_text"] = body["csv_text"].replace(",Yes,", ",maybe,")
    elif change == "status":
        body["completed_statuses"] = ["not-a-real-status"]
    else:
        body["columns"] = {"status": ""}
    response, _, plan = commit(client, o, base, body)
    assert not plan["ready"]
    assert response.status_code == 422, response.text
    assert client.get(base + "/devpost/projects", headers=o.headers).json() == []
    assert client.get(base + "/manage", headers=o.headers).json()["presentations"] == []


def test_preview_detects_stale_config_and_team_state(client, setup_import, engine):
    o, _, event, group, base = setup_import
    body = payload(group.code)
    plan = client.post(base + "/devpost/preview", headers=o.headers, json=body).json()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE event_operations SET version=version+1 WHERE event_id=:id"),
            {"id": event},
        )
    response = client.post(
        base + "/devpost/import",
        headers=o.headers,
        json={
            **body,
            "preview_digest": plan["digest"],
            "operation_id": str(uuid4()),
            "reason": "Final export",
        },
    )
    assert response.status_code == 409
    assert client.get(base + "/devpost/projects", headers=o.headers).json() == []


def test_semicolon_custom_columns_and_explicit_complete_export(client, setup_import):
    o, _, _, group, base = setup_import
    body = {
        "csv_text": f'Link;Name;Code;Track\nhttps://devpost.com/software/new;"A multiline\nproject";{group.code};Agriculture\n',
        "columns": {
            "url": "Link",
            "title": "Name",
            "team": "Code",
            "challenge": "Track",
        },
        "challenges": {"Agriculture": "c1"},
        "completed_only": True,
    }
    response, _, _ = commit(client, o, base, body)
    assert response.status_code == 200, response.text
    assert response.json()["created_turns"] == 1
    assert client.post(base + "/schedule", headers=o.headers).status_code == 200
    turns = client.get(base + "/manage", headers=o.headers).json()["presentations"]
    assert len(turns) == 1 and turns[0]["scheduled_at"]


def test_relink_is_rejected_and_mlh_changes_preserve_queue(
    client, setup_import, create_user, create_group
):
    o, _, event, group, base = setup_import
    assert commit(client, o, base, payload(group.code))[0].status_code == 200
    other = create_group(event, [create_user()])
    response, _, plan = commit(client, o, base, payload(other.code))
    assert response.status_code == 422 and not plan["ready"]
    body = payload(group.code)
    body["csv_text"] = body["csv_text"].replace(",Yes,", ",No,")
    response, _, plan = commit(client, o, base, body)
    assert response.status_code == 200
    assert any("differs" in w for w in plan["rows"][0]["warnings"])
    assert (
        len(client.get(base + "/manage", headers=o.headers).json()["presentations"])
        == 2
    )


def test_csv_structure_and_limits(client, setup_import):
    o, _, _, _, base = setup_import
    for csv_text in [
        "",
        "a,a\n1,2",
        "a,b\n1,2,3",
        "a,b\n\x00,2",
        "a\n" + "row\n" * 2001,
    ]:
        response = client.post(
            base + "/devpost/preview", headers=o.headers, json={"csv_text": csv_text}
        )
        assert response.status_code == 422, response.text
