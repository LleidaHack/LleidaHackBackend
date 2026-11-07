from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text


def test_approval_permissions_history_and_legacy_bypass(client, create_user, engine):
    user, admin, staff = (
        create_user(),
        create_user(role="admin"),
        create_user(role="lleidahacker"),
    )
    path = "/v1/nicknames"
    original = client.get(path + "/me", headers=user.headers).json()["nickname"]
    proposal = client.post(
        path + "/me", headers=user.headers, json={"nickname": "Tractor Hero"}
    )
    assert proposal.status_code == 200, proposal.text
    item = proposal.json()
    assert client.get(path + "/me", headers=user.headers).json()["nickname"] == original
    assert (
        client.post(
            path + "/me", headers=user.headers, json={"nickname": "Again"}
        ).status_code
        == 409
    )
    assert (
        client.put(
            f"/v1/hacker/{user.id}", headers=user.headers, json={"nickname": "Bypass"}
        ).status_code
        == 403
    )
    for actor in (user, staff):
        assert client.get(path + "/requests", headers=actor.headers).status_code == 403
        assert (
            client.post(
                path + f"/requests/{item['id']}",
                headers=actor.headers,
                json={"action": "approve"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                path + f"/users/{user.id}",
                headers=actor.headers,
                json={"nickname": "Bypass"},
            ).status_code
            == 403
        )
    response = client.post(
        path + f"/requests/{item['id']}",
        headers=admin.headers,
        json={"action": "approve"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["actor_id"] == admin.id and response.json()["resolved_at"]
    assert (
        client.get(path + "/me", headers=user.headers).json()["nickname"]
        == "Tractor Hero"
    )
    assert (
        client.post(
            path + f"/requests/{item['id']}",
            headers=admin.headers,
            json={"action": "reject"},
        ).status_code
        == 409
    )
    with engine.connect() as conn:
        assert (
            conn.execute(
                text("select count(*) from coin_movement where user_id=:id"),
                {"id": user.id},
            ).scalar()
            == 0
        )


def test_conflicts_rejection_correction_and_validation(client, create_user):
    one, two, admin = create_user(), create_user(), create_user(role="admin")
    base = "/v1/nicknames"
    for name in ("<script>", "a", "abc\u202edef", " " * 4):
        assert (
            client.post(
                base + "/me", headers=one.headers, json={"nickname": name}
            ).status_code
            == 422
        )
    ids = []
    for user in (one, two):
        response = client.post(
            base + "/me", headers=user.headers, json={"nickname": "SameName"}
        )
        ids.append(response.json()["id"])
    assert (
        client.post(
            base + f"/requests/{ids[0]}",
            headers=admin.headers,
            json={"action": "approve"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            base + f"/requests/{ids[1]}",
            headers=admin.headers,
            json={"action": "approve"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            base + f"/requests/{ids[1]}",
            headers=admin.headers,
            json={"action": "reject"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            base + "/me", headers=two.headers, json={"nickname": "samename"}
        ).status_code
        == 409
    )
    client.post(base + "/me", headers=two.headers, json={"nickname": "Pending"})
    result = client.post(
        base + f"/users/{two.id}", headers=admin.headers, json={"nickname": "SafeName"}
    )
    assert result.status_code == 200, result.text
    state = client.get(base + "/me", headers=two.headers).json()
    assert state["nickname"] == "SafeName"
    assert [r["status"] for r in state["requests"]] == [
        "corrected",
        "superseded",
        "rejected",
    ]


def test_concurrent_request_has_one_pending(client, create_user):
    user = create_user()

    def submit(index):
        return client.post(
            "/v1/nicknames/me",
            headers=user.headers,
            json={"nickname": f"Tractor{index}"},
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [200, 409]
