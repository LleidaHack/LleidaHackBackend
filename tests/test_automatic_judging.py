# ruff: noqa: F811
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session
from test_challenge_votes import control, voting  # noqa: F401

from src.impl.Operations.model import EventOperations, Presentation
from src.impl.Operations.service import effective_phase


@pytest.mark.parametrize(
    "phase,delta,expected",
    [
        ("hacking", 1, "hacking"),
        ("hacking", 0, "judging"),
        ("hacking", -1, "judging"),
        ("preparation", -1, "preparation"),
        ("finished", -1, "finished"),
        ("judging", 100, "judging"),
    ],
)
def test_deadline_boundary(phase, delta, expected):
    now = datetime.now(UTC)
    assert (
        effective_phase(
            {"phase": phase, "deadline": (now + timedelta(seconds=delta)).isoformat()},
            now,
        )
        == expected
    )


def test_missing_deadline_does_not_start_judging():
    for deadline in (None, "", "invalid"):
        assert effective_phase({"phase": "hacking", "deadline": deadline}) == "hacking"


def test_public_judging_transition_preserves_publication_gate(client, voting, engine):
    organizer, _, _, _, event, group, base = voting
    with Session(engine) as session:
        row = session.get(EventOperations, event)
        row.config = {
            **row.config,
            "phase": "hacking",
            "deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
            "rooms": [{"id": "one", "title": "Secret Room"}],
        }
        session.add(
            Presentation(event_id=event, group_id=group.id, room="one", track="one")
        )
        session.commit()
    hidden = client.get(base + "/public").json()
    assert hidden["phase"] == "judging"
    assert hidden["rooms"] == hidden["presentations"] == []
    assert "Secret Room" not in str(hidden)
    assert control(client, organizer, base, True, False).status_code == 200
    visible = client.get(base + "/public").json()
    assert visible["phase"] == "judging" and len(visible["presentations"]) == 1
    assert (
        client.get(base + "/manage", headers=organizer.headers).json()["phase"]
        == "hacking"
    )
    # Extending the deadline returns the public screen to hacking and hides queues.
    with Session(engine) as session:
        row = session.get(EventOperations, event)
        row.config = {
            **row.config,
            "deadline": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }
        session.commit()
    extended = client.get(base + "/public").json()
    assert extended["phase"] == "hacking" and extended["presentations"] == []
