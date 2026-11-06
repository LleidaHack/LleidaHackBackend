import pytest
from sqlalchemy import text


@pytest.fixture
def voting(client, create_user, create_event, create_group):
    organizer = create_user(role="organizer")
    member = create_user()
    teammate = create_user()
    outsider = create_user()
    event = create_event([member, teammate, outsider])
    group = create_group(event, [member, teammate])
    base = f"/v1/operations/{event}"
    config = client.get(base + "/manage", headers=organizer.headers).json()
    config["challenges"] = [
        {"id": "one", "title": "First", "published": True},
        {"id": "two", "title": "Second", "published": True},
        {"id": "draft", "title": "Secret draft", "published": False},
    ]
    response = client.put(
        base + "/config",
        headers=organizer.headers,
        json={
            "version": config["version"],
            "config": config,
            "reason": "Set challenges",
        },
    )
    assert response.status_code == 200
    return organizer, member, teammate, outsider, event, group, base


def control(client, organizer, base, published, opened):
    config = client.get(base + "/manage", headers=organizer.headers).json()
    return client.put(
        base + "/challenge-controls",
        headers=organizer.headers,
        json={
            "version": config["version"],
            "challenges_released": published,
            "challenge_votes_open": opened,
            "reason": "Update publication and voting",
        },
    )


def test_publication_and_open_close_are_enforced(client, voting):
    o, member, _, _, _, group, base = voting
    endpoint = base + f"/teams/{group.id}/challenge-vote"
    assert client.get(base + "/public").json()["challenges"] == []
    assert client.get(endpoint, headers=member.headers).json()["challenges"] == []
    assert control(client, o, base, False, True).status_code == 422
    assert control(client, o, base, True, False).status_code == 200
    assert len(client.get(base + "/public").json()["challenges"]) == 2
    assert (
        client.put(
            endpoint, headers=member.headers, json={"challenge": "one", "version": 0}
        ).status_code
        == 409
    )
    assert control(client, o, base, True, True).status_code == 200
    assert (
        client.put(
            endpoint, headers=member.headers, json={"challenge": "draft", "version": 0}
        ).status_code
        == 422
    )
    response = client.put(
        endpoint, headers=member.headers, json={"challenge": "one", "version": 0}
    )
    assert response.status_code == 200, response.text
    assert control(client, o, base, False, False).status_code == 200
    assert client.get(base + "/public").json()["challenges"] == []
    assert (
        client.put(
            endpoint, headers=member.headers, json={"challenge": "two", "version": 1}
        ).status_code
        == 409
    )
    assert client.get(endpoint, headers=member.headers).json()["choice"] == "one"


def test_one_choice_per_team_concurrent_stale_edits_and_no_queue(
    client, voting, engine
):
    o, member, teammate, outsider, _event, group, base = voting
    endpoint = base + f"/teams/{group.id}/challenge-vote"
    assert control(client, o, base, True, True).status_code == 200
    for actor in (outsider, o):
        assert client.get(endpoint, headers=actor.headers).status_code == 403
        assert (
            client.put(
                endpoint, headers=actor.headers, json={"challenge": "one", "version": 0}
            ).status_code
            == 403
        )
    assert (
        client.put(
            endpoint, headers=member.headers, json={"challenge": "one", "version": 0}
        ).status_code
        == 200
    )
    assert (
        client.put(
            endpoint, headers=teammate.headers, json={"challenge": "two", "version": 0}
        ).status_code
        == 409
    )
    assert (
        client.put(
            endpoint, headers=teammate.headers, json={"challenge": "two", "version": 1}
        ).status_code
        == 200
    )
    # A repeat selection is a no-op and does not inflate counts or audit events.
    assert (
        client.put(
            endpoint, headers=teammate.headers, json={"challenge": "two", "version": 2}
        ).status_code
        == 200
    )
    result = client.get(base + "/challenge-votes", headers=o.headers).json()
    assert result["voted"] == 1 and result["total_teams"] == 1
    assert [c["count"] for c in result["challenges"]] == [0, 1, 0]
    assert (
        client.get(base + "/challenge-votes", headers=member.headers).status_code == 403
    )
    assert client.get(base + "/manage", headers=o.headers).json()["presentations"] == []
    audit = client.get(base + "/audit?action=challenge.vote", headers=o.headers).json()
    assert len(audit) == 2 and audit[0]["actor_id"] == teammate.id
    assert audit[0]["details"]["before"] == "one"
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM hacker_group_user WHERE group_id=:g AND hacker_id=:h"),
            {"g": group.id, "h": member.id},
        )
    assert (
        client.put(
            endpoint, headers=member.headers, json={"challenge": "one", "version": 2}
        ).status_code
        == 403
    )


def test_controls_require_management_and_fresh_version(client, voting):
    o, member, _, _, _, _, base = voting
    config = client.get(base + "/manage", headers=o.headers).json()
    body = {
        "version": config["version"],
        "challenges_released": True,
        "challenge_votes_open": True,
        "reason": "Start voting",
    }
    assert (
        client.put(
            base + "/challenge-controls", headers=member.headers, json=body
        ).status_code
        == 403
    )
    assert (
        client.put(
            base + "/challenge-controls", headers=o.headers, json=body
        ).status_code
        == 200
    )
    assert (
        client.put(
            base + "/challenge-controls", headers=o.headers, json=body
        ).status_code
        == 409
    )
    config = client.get(base + "/manage", headers=o.headers).json()
    config["challenges_released"] = False
    assert (
        client.put(
            base + "/config",
            headers=o.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Invalid direct config",
            },
        ).status_code
        == 422
    )
