"""Assert that unreleased challenge data never crosses public/scanner boundaries."""

import json

import pytest
from sqlalchemy import text
from test_challenge_votes import control, voting  # noqa: F401


@pytest.fixture
def secrets(client, voting, engine):  # noqa: F811
    organizer, _member, _teammate, _outsider, event, _group, base = voting
    config = client.get(base + "/manage", headers=organizer.headers).json()
    config.update(
        challenges=[
            {
                "id": "SECRET_TRACK",
                "title": "SECRET_TITLE",
                "description": "SECRET_DESCRIPTION",
                "published": True,
                "resources": [
                    {
                        "title": "SECRET_RESOURCE",
                        "url": "https://example.org/SECRET_FILE.pdf",
                    }
                ],
            }
        ],
        decoy_challenges=[
            {
                "id": "bait",
                "title": "Tractor on Mars",
                "description": "Build a space tractor",
                "published": True,
            },
            {"id": "draft-bait", "title": "Draft bait", "published": False},
        ],
        rooms=[{"id": "SECRET_TRACK", "title": "SECRET_ROOM"}],
        phase="hacking",
    )
    response = client.put(
        base + "/config",
        headers=organizer.headers,
        json={
            "version": config["version"],
            "config": config,
            "reason": "Prepare secret challenges",
        },
    )
    assert response.status_code == 200, response.text
    # A future management property must not become public through an accidental copy.
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE event_operations SET config=(config::jsonb || :extra)::json WHERE event_id=:event"
            ),
            {"event": event, "extra": json.dumps({"internal_notes": "SECRET_NOTES"})},
        )
    return voting


def assert_no_secrets(response):
    assert response.status_code == 200, response.text
    assert "SECRET_" not in response.text
    assert "decoy_challenges" not in response.text
    assert "no-store" in response.headers["cache-control"]


def test_public_endpoints_only_return_published_decoys(client, secrets):
    *_, base = secrets
    for endpoint in (
        "/public",
        "/public?private=true&challenges_released=true",
        "/challenges",
    ):
        response = client.get(base + endpoint)
        assert_no_secrets(response)
        assert [c["id"] for c in response.json()["challenges"]] == ["bait"]
    response = client.get(base + "/public").json()
    assert response["rooms"] == [] and response["presentations"] == []
    assert not response["challenge_votes_open"]


def test_release_and_rehide_are_atomic_and_do_not_cache(client, secrets):
    organizer, member, _, _, _, group, base = secrets
    assert control(client, organizer, base, True, True).status_code == 200
    response = client.get(base + "/challenges")
    assert response.json()["challenges"][0]["id"] == "SECRET_TRACK"
    assert "bait" not in response.text
    assert "no-store" in response.headers["cache-control"]
    endpoint = base + f"/teams/{group.id}/challenge-vote"
    assert (
        client.put(
            endpoint,
            headers=member.headers,
            json={"challenge": "SECRET_TRACK", "version": 0},
        ).status_code
        == 200
    )
    assert control(client, organizer, base, False, False).status_code == 200
    assert_no_secrets(client.get(endpoint, headers=member.headers))
    assert_no_secrets(client.get(base + "/public"))
    # Only administrators can retrieve the originals and their resource URLs.
    assert "SECRET_FILE" in client.get(base + "/manage", headers=organizer.headers).text


@pytest.mark.parametrize("role", ["hacker", "lleidahacker"])
def test_non_management_roles_cannot_read_or_publish_originals(
    client, secrets, create_user, role
):
    organizer, _, _, _, _, _, base = secrets
    actor = create_user(role=role)
    config = client.get(base + "/manage", headers=organizer.headers).json()
    for endpoint in ("/manage", "/audit", "/challenge-votes", "/devpost/projects"):
        response = client.get(base + endpoint, headers=actor.headers)
        assert response.status_code == 403
        assert "SECRET_" not in response.text
    response = client.put(
        base + "/challenge-controls",
        headers=actor.headers,
        json={
            "version": config["version"],
            "challenges_released": True,
            "challenge_votes_open": False,
            "reason": "Unauthorized reveal",
        },
    )
    assert response.status_code == 403
    if role == "lleidahacker":
        assert_no_secrets(client.get(base + "/scanner", headers=actor.headers))


def test_admin_cannot_bypass_superadmin_release_via_config(
    client, secrets, create_user
):
    *_, base = secrets
    admin = create_user(role="admin")
    config = client.get(base + "/manage", headers=admin.headers).json()
    assert "SECRET_TITLE" in str(config)
    assert control(client, admin, base, True, False).status_code == 403
    config["challenges_released"] = True
    response = client.put(
        base + "/config",
        headers=admin.headers,
        json={
            "version": config["version"],
            "config": config,
            "reason": "Try alternate publish path",
        },
    )
    assert response.status_code == 403
    assert_no_secrets(client.get(base + "/public"))


def test_missing_release_flag_and_judging_phase_fail_closed(client, secrets, engine):
    _, member, _, _, event, group, base = secrets
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE event_operations SET config=((config::jsonb - 'challenges_released') || '{\"phase\":\"judging\"}'::jsonb)::json WHERE event_id=:event"
            ),
            {"event": event},
        )
    assert_no_secrets(client.get(base + "/public"))
    assert_no_secrets(
        client.get(base + f"/teams/{group.id}/challenge-vote", headers=member.headers)
    )
    assert client.get(base + "/public").json()["rooms"] == []


def test_hidden_challenge_ids_cannot_be_probed_through_enrollment(client, secrets):
    _, member, _, _, _, group, base = secrets
    results = []
    for challenge in ("SECRET_TRACK", "missing", "bait"):
        response = client.post(
            base + f"/teams/{group.id}/enroll",
            headers=member.headers,
            json={"challenge": challenge, "mlh": False},
        )
        results.append((response.status_code, response.json()))
    assert results[0] == results[1] == results[2]
    assert results[0][0] == 403


def test_anonymous_cannot_retrieve_management_data(client, secrets):
    *_, base = secrets
    for endpoint in (
        "/manage",
        "/audit",
        "/challenge-votes",
        "/devpost/projects",
        "/scanner",
    ):
        response = client.get(base + endpoint)
        assert response.status_code in (401, 403)
        assert "SECRET_" not in response.text
