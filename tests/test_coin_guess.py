# ruff: noqa: F811
from uuid import uuid4

from tests.test_tickets_vouchers import accept, user_code  # noqa: F401


def test_coin_guess_activity_notes_latest_guess_per_person(
    client, create_user, create_event, accept, engine, monkeypatch
):
    from src.configuration.Settings import settings

    monkeypatch.setattr(settings.rate_limit, "enabled", False)
    admin, staff = create_user(role="organizer"), create_user(role="lleidahacker")
    users = [create_user(name=f"Hacker {i}") for i in range(2)]
    event = create_event(users)
    base = f"/v1/operations/{event}"

    def activity(id, **flags):
        return {
            "id": id,
            "title": id,
            "start": "2026-11-28T12:00:00Z",
            "end": "2026-11-28T14:00:00Z",
            **flags,
        }

    def save(activities, reason="Set up activities"):
        current = client.get(base + "/manage", headers=admin.headers).json()
        current["activities"] = activities
        return client.put(
            base + "/config",
            headers=admin.headers,
            json={"config": current, "version": current["version"], "reason": reason},
        )

    assert save([activity("both", timed=True, coin_guess=True)]).status_code == 422
    response = save([activity("jar", coin_guess=True), activity("talk")])
    assert response.status_code == 200, response.text
    badges = []
    for user in users:
        accept(admin, event, user)
        badge = client.post(
            f"/v1/event/{event}/vouchers/generate",
            headers=admin.headers,
            json={"count": 1},
        ).json()["vouchers"][0]["code"]
        assert (
            client.put(
                f"/v1/event/{event}/vouchers/{badge}/assign/{user_code(engine, user)}",
                headers=staff.headers,
            ).status_code
            == 200
        )
        badges.append(badge)

    def scan(i=0, guess=120, target="jar", op=None, kind="activity"):
        body = {
            "kind": kind,
            "code": badges[i],
            "target": target,
            "operation_id": op or str(uuid4()),
        }
        if guess is not None:
            body["guess"] = guess
        return client.post(base + "/scan", headers=staff.headers, json=body)

    for guess in [None, -1, 1000001, 12.5, True, "120"]:
        assert scan(guess=guess).status_code == 422
    assert scan(target="talk").status_code == 422
    assert scan(kind="checkin").status_code == 422
    op = str(uuid4())
    first = scan(op=op)
    assert first.status_code == 200, first.text
    assert first.json()["guess"] == 120
    assert scan(op=op).json() == first.json()
    assert scan(op=op, guess=121).status_code == 409
    # Scanning the same person again corrects the guess.
    assert scan(guess=150).status_code == 200
    assert scan(i=1, guess=0).status_code == 200
    assert scan(i=1, guess=None, target="talk").status_code == 200

    path = base + "/activities/jar/guesses"
    assert client.get(path, headers=staff.headers).status_code == 403
    assert (
        client.get(
            base + "/activities/missing/guesses", headers=admin.headers
        ).status_code
        == 404
    )
    listed = client.get(path, headers=admin.headers).json()
    assert listed["activity"] == "jar"
    assert [(p["name"], p["guess"], p["scans"]) for p in listed["participants"]] == [
        ("Hacker 0", 150, 2),
        ("Hacker 1", 0, 1),
    ]
    assert "'guess':" not in str(client.get(base + "/public").json())

    # An older management client omitting the new flag must preserve it.
    current = client.get(base + "/manage", headers=admin.headers).json()
    for a in current["activities"]:
        a.pop("coin_guess", None)
    updated = save(current["activities"], "Older client saves configuration")
    assert updated.status_code == 200, updated.text
    assert updated.json()["activities"][0]["coin_guess"] is True
