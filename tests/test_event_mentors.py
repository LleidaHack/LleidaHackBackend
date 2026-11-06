from uuid import uuid4


def test_mentor_roster_badges_meals_rounds_and_restrictions(
    client, create_user, create_event
):
    admin, staff, hacker = (
        create_user(role="organizer"),
        create_user(role="lleidahacker"),
        create_user(),
    )
    event = create_event()
    base = f"/v1/operations/{event}"
    assert (
        client.post(
            base + "/mentors", headers=staff.headers, json={"name": "Mentor Test"}
        ).status_code
        == 403
    )
    result = client.post(
        base + "/mentors", headers=admin.headers, json={"name": "Mentor Test"}
    )
    assert result.status_code == 200, result.text
    mentor = result.json()["id"]
    profile = client.get(f"/v1/user/{mentor}", headers=admin.headers)
    assert profile.status_code == 200, profile.text
    assert (
        profile.json()["type"] == "mentor" and profile.json()["access_role"] == "mentor"
    )
    assert client.get(base + "/mentors", headers=hacker.headers).status_code == 403
    assert (
        client.get(base + "/scanner", headers=staff.headers).json()["mentors"][0][
            "name"
        ]
        == "Mentor Test"
    )
    vouchers = client.post(
        f"/v1/event/{event}/vouchers/generate", headers=admin.headers, json={"count": 2}
    ).json()["vouchers"]
    code, replacement = [v["code"] for v in vouchers]
    endpoint = base + f"/mentors/{mentor}/badge"
    assert (
        client.put(endpoint, headers=hacker.headers, json={"code": code}).status_code
        == 403
    )
    assert (
        client.put(endpoint, headers=staff.headers, json={"code": code}).status_code
        == 200
    )
    assert (
        client.put(endpoint, headers=staff.headers, json={"code": code}).status_code
        == 200
    )
    meal = client.post(
        "/v1/meal/",
        headers=admin.headers,
        json={"name": "Dinner", "description": "", "event_id": event},
    ).json()["id"]

    def scan(kind="meal", badge=code, round=1, actor=staff):
        return client.post(
            base + "/scan",
            headers=actor.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": kind,
                "code": badge,
                "target": str(meal),
                "round": round,
            },
        )

    assert scan().status_code == 200
    assert scan().status_code == 409
    for kind in ("activity", "redeem", "judging_start", "checkin"):
        assert scan(kind).status_code == 403
    assert scan("award", actor=admin).status_code == 403
    assert (
        client.put(
            endpoint, headers=staff.headers, json={"code": replacement, "replace": True}
        ).status_code
        == 403
    )
    assert (
        client.put(
            endpoint, headers=admin.headers, json={"code": replacement, "replace": True}
        ).status_code
        == 200
    )
    assert scan().status_code == 404
    assert scan(badge=replacement).status_code == 409
    assert (
        client.post(
            base + f"/meals/{meal}/round",
            headers=admin.headers,
            json={"expected_round": 1, "action": "next", "reason": "Allow seconds"},
        ).status_code
        == 200
    )
    assert scan(badge=replacement, round=2).status_code == 200
    assert client.get(base + "/public").json()["leaderboard"] == []
    assert (
        client.patch(
            base + f"/mentors/{mentor}", headers=admin.headers, json={"active": False}
        ).status_code
        == 200
    )
    assert scan(badge=replacement, round=2).status_code == 403
    assert client.get(base + "/scanner", headers=staff.headers).json()["mentors"] == []
    assert client.get(base + "/audit", headers=admin.headers).status_code == 200


def test_existing_mentor_role_has_no_management_or_participant_privileges(
    client, create_user, create_event
):
    admin, user = create_user(role="organizer"), create_user()
    event = create_event()
    response = client.patch(
        f"/v1/access/users/{user.id}/role",
        headers=admin.headers,
        json={"role": "mentor", "reason": "Mentor assignment"},
    )
    assert response.status_code == 200, response.text
    for path in (
        f"/v1/operations/{event}/manage",
        f"/v1/operations/{event}/scanner",
        f"/v1/operations/{event}/wallet",
        "/v1/user/all",
    ):
        assert client.get(path, headers=user.headers).status_code == 403
    assert client.get("/v1/auth/me", headers=user.headers).status_code == 200
    response = client.post(
        f"/v1/operations/{event}/mentors",
        headers=admin.headers,
        json={"name": "Existing mentor", "user_id": user.id},
    )
    assert response.status_code == 200, response.text
    assert response.json()["id"] == user.id
