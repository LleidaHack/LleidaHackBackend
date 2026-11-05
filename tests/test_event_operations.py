# ruff: noqa: F811
from uuid import uuid4

from tests.test_tickets_vouchers import accept, user_code  # noqa: F401


def prepare(client, create_user, create_event, accept, engine):
    organizer = create_user(role="organizer")
    hacker = create_user()
    event = create_event([hacker])
    accept(organizer, event, hacker)
    code = user_code(engine, hacker)
    response = client.put(
        f"/v1/event/{event}/participate/{code}", headers=organizer.headers
    )
    assert response.status_code == 200, response.text
    meal = client.post(
        "/v1/meal/",
        headers=organizer.headers,
        json={"name": "Dinner", "description": "", "event_id": event},
    ).json()["id"]
    return organizer, hacker, event, code, meal


def test_rounds_duplicate_replay_and_audit(
    client, create_user, create_event, accept, engine
):
    o, h, event, code, meal = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    body = {
        "operation_id": str(uuid4()),
        "kind": "meal",
        "code": code,
        "target": str(meal),
        "round": 1,
        "device": "phone-a",
    }
    first = client.post(url + "/scan", headers=o.headers, json=body)
    assert first.status_code == 200, first.text
    assert (
        client.post(url + "/scan", headers=o.headers, json=body).json() == first.json()
    )
    body["operation_id"] = str(uuid4())
    assert client.post(url + "/scan", headers=o.headers, json=body).status_code == 409
    assert (
        client.post(
            url + f"/meals/{meal}/round",
            headers=o.headers,
            json={
                "expected_round": 1,
                "action": "next",
                "reason": "Extra food available",
            },
        ).status_code
        == 200
    )
    body["operation_id"] = str(uuid4())
    assert client.post(url + "/scan", headers=o.headers, json=body).status_code == 409
    body.update(round=2, operation_id=str(uuid4()))
    assert client.post(url + "/scan", headers=o.headers, json=body).status_code == 200
    body["operation_id"] = str(uuid4())
    assert client.post(url + "/scan", headers=o.headers, json=body).status_code == 409
    entries = client.get(url + "/audit", headers=o.headers).json()
    assert (
        len([a for a in entries if a["action"] == "meal" and a["outcome"] == "success"])
        == 2
    )
    assert len([a for a in entries if a["outcome"] == "rejected"]) == 3
    assert client.get(url + "/audit", headers=h.headers).status_code == 403


def test_coins_cannot_double_spend_and_corrections_are_linked(
    client, create_user, create_event, accept, engine
):
    o, h, event, code, _ = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    config = client.get(url + "/manage", headers=o.headers).json()
    config["prizes"] = [{"id": "mug", "title": "Mug", "cost": 30, "stock": 1}]
    assert (
        client.put(
            url + "/config",
            headers=o.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Set prizes",
            },
        ).status_code
        == 200
    )

    def scan(**kw):
        return client.post(
            url + "/scan",
            headers=o.headers,
            json={"operation_id": str(uuid4()), "code": code, **kw},
        )

    assert (
        scan(kind="award", amount=50, reason="Activity winner").json()["balance"] == 50
    )
    assert scan(kind="redeem", target="mug").json()["balance"] == 20
    assert scan(kind="redeem", target="mug").status_code == 409
    wallet = client.get(url + "/wallet", headers=h.headers).json()
    assert wallet["balance"] == 20
    assert client.get(url + "/public").json()["leaderboard"][0]["balance"] == 20
    debit = wallet["movements"][0]["id"]
    assert (
        scan(kind="reverse", target=str(debit), reason="Prize return").json()["balance"]
        == 50
    )
    assert (
        scan(kind="reverse", target=str(debit), reason="Duplicate return").status_code
        == 409
    )
    assert scan(kind="award", amount=0, reason="No amount").status_code == 422
    assert client.get(url + "/public").json()["leaderboard"][0]["balance"] == 50


def test_private_content_hidden_and_config_conflicts(
    client, create_user, create_event, accept, engine
):
    o, h, event, _code, _ = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    config = client.get(url + "/manage", headers=o.headers).json()
    config["challenges"] = [{"id": "secret", "title": "Secret", "published": False}]
    config["stream_url"] = "https://twitch.tv/lleidahack"
    config["wifi_name"] = "Demo network"
    config["wifi_instructions"] = "Ask organization for access"
    config["wifi_guide_url"] = "https://example.test/wifi"
    body = {
        "version": config["version"],
        "config": config,
        "reason": "Prepare challenge",
    }
    assert client.put(url + "/config", headers=o.headers, json=body).status_code == 200
    assert client.put(url + "/config", headers=o.headers, json=body).status_code == 409
    public = client.get(url + "/public").json()
    assert public["challenges"] == [] and public["presentations"] == []
    assert public["wifi_name"] == "Demo network"
    assert public["wifi_instructions"] == "Ask organization for access"
    assert public["stream_url"] == "https://twitch.tv/lleidahack"
    assert public["wifi_guide_url"] == "https://example.test/wifi"
    assert "teams" not in public and "meal_rounds" not in public
    assert client.get(url + "/manage", headers=h.headers).status_code == 403


def test_judging_scheduler_prevents_mlh_overlap_and_detects_stale_edits(
    client, create_user, create_event, create_group, accept, engine
):
    from datetime import UTC, datetime, timedelta

    o, h, event, _code, _meal = prepare(
        client, create_user, create_event, accept, engine
    )
    group = create_group(event, [h])
    url = f"/v1/operations/{event}"
    config = client.get(url + "/manage", headers=o.headers).json()
    start = datetime.now(UTC) + timedelta(hours=1)
    config.update(
        challenges=[{"id": "c1", "title": "Challenge", "published": True}],
        rooms=[{"id": "c1", "title": "Room 1"}, {"id": "mlh", "title": "MLH"}],
        judging_start=start.isoformat(),
        judging_end=(start + timedelta(hours=2)).isoformat(),
        phase="hacking",
    )
    assert (
        client.put(
            url + "/config",
            headers=o.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Set judging",
            },
        ).status_code
        == 200
    )
    response = client.post(
        url + f"/teams/{group.id}/enroll",
        headers=h.headers,
        json={"challenge": "c1", "mlh": True},
    )
    assert response.status_code == 200, response.text
    response = client.post(url + "/schedule", headers=o.headers)
    assert response.status_code == 200, response.text
    turns = response.json()["presentations"]
    assert len(turns) == 2
    assert abs(
        datetime.fromisoformat(turns[0]["scheduled_at"])
        - datetime.fromisoformat(turns[1]["scheduled_at"])
    ) >= timedelta(minutes=15)
    body = {**turns[0], "pinned": True, "reason": "Pin this time"}
    assert (
        client.patch(
            url + f"/presentations/{turns[0]['id']}", headers=o.headers, json=body
        ).status_code
        == 200
    )
    assert (
        client.patch(
            url + f"/presentations/{turns[0]['id']}", headers=o.headers, json=body
        ).status_code
        == 409
    )
    assert client.get(url + "/public").json()["presentations"] == []


def test_concurrent_meal_scans_only_deliver_once(
    client, app, create_user, create_event, accept, engine
):
    from concurrent.futures import ThreadPoolExecutor

    o, _h, event, code, meal = prepare(
        client, create_user, create_event, accept, engine
    )

    def scan(index):
        return client.post(
            f"/v1/operations/{event}/scan",
            headers=o.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": "meal",
                "code": code,
                "target": str(meal),
                "round": 1,
                "device": f"phone-{index}",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(scan, range(2)))
    assert sorted(statuses) == [200, 409]


def test_concurrent_redemptions_cannot_spend_same_balance(
    client, app, create_user, create_event, accept, engine
):
    client._transport.raise_server_exceptions = True
    from concurrent.futures import ThreadPoolExecutor

    o, h, event, code, _ = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    config = client.get(url + "/manage", headers=o.headers).json()
    config["prizes"] = [{"id": "mug", "title": "Mug", "cost": 30, "stock": 2}]
    assert (
        client.put(
            url + "/config",
            headers=o.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Set prizes",
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            url + "/scan",
            headers=o.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": "award",
                "code": code,
                "amount": 50,
                "reason": "Test award",
            },
        ).status_code
        == 200
    )

    def redeem(index):
        return client.post(
            url + "/scan",
            headers=o.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": "redeem",
                "code": code,
                "target": "mug",
                "device": f"phone-{index}",
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(redeem, range(2)))
    assert sorted(statuses) == [200, 409]
    assert client.get(url + "/wallet", headers=h.headers).json()["balance"] == 20
    assert (
        client.get(url + "/manage", headers=o.headers).json()["prizes"][0]["stock"] == 1
    )


def test_hackers_cannot_mint_coins_or_override_server_rewards(
    client, create_user, create_event, accept, engine
):
    o, h, event, code, _ = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    payload = {
        "operation_id": str(uuid4()),
        "kind": "award",
        "code": code,
        "amount": 999999,
        "reason": "I am admin",
    }
    response = client.post(url + "/scan", headers=h.headers, json=payload)
    assert response.status_code == 403
    assert "tractor" in response.json()["detail"]
    for tampering in [
        {"user_id": h.id},
        {"is_admin": True},
        {"balance": 99999},
        {"amount": True},
        {"amount": -1},
        {"amount": 1.5},
    ]:
        response = client.post(
            url + "/scan",
            headers=h.headers,
            json={**payload, "operation_id": str(uuid4()), **tampering},
        )
        assert response.status_code == 422, response.text
        assert response.json()["code"] == "TRACTOR_NOT_A_MINT"
    assert client.get(url + "/wallet", headers=h.headers).json()["balance"] == 0
    entries = client.get(url + "/audit", headers=o.headers).json()
    assert len([a for a in entries if a["action"] == "security.invalid_scan"]) == 6
    assert all("DEMO" not in str(a["details"]) for a in entries)
    assert client.get(url + "/audit", headers=h.headers).status_code == 403
    assert client.post(url + "/scan", json=payload).status_code in (401, 403)


def test_activity_points_are_server_owned_and_only_granted_once(
    client, create_user, create_event, accept, engine
):
    from datetime import UTC, datetime, timedelta

    o, h, event, code, _ = prepare(client, create_user, create_event, accept, engine)
    url = f"/v1/operations/{event}"
    config = client.get(url + "/manage", headers=o.headers).json()
    now = datetime.now(UTC)
    config["activities"] = [
        {
            "id": "workshop",
            "title": "Workshop",
            "start": now.isoformat(),
            "end": (now + timedelta(hours=1)).isoformat(),
            "points": 10,
        }
    ]
    assert (
        client.put(
            url + "/config",
            headers=o.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Configure workshop",
            },
        ).status_code
        == 200
    )
    payload = {
        "operation_id": str(uuid4()),
        "kind": "activity",
        "code": code,
        "target": "workshop",
    }
    assert (
        client.post(
            url + "/scan", headers=o.headers, json={**payload, "amount": 10000}
        ).status_code
        == 422
    )
    assert (
        client.post(url + "/scan", headers=o.headers, json=payload).json()["balance"]
        == 10
    )
    assert (
        client.post(
            url + "/scan",
            headers=o.headers,
            json={**payload, "operation_id": str(uuid4())},
        ).status_code
        == 409
    )
    assert (
        client.post(
            url + "/scan",
            headers=o.headers,
            json={**payload, "round": 2, "operation_id": str(uuid4())},
        ).status_code
        == 422
    )
    assert client.get(url + "/wallet", headers=h.headers).json()["balance"] == 10


def test_meal_correction_preserves_history_and_allows_replacement(
    client, create_user, create_event, accept, engine
):
    o, _h, event, code, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    url = f"/v1/operations/{event}"
    payload = {
        "operation_id": str(uuid4()),
        "kind": "meal",
        "code": code,
        "target": str(meal),
    }
    assert (
        client.post(url + "/scan", headers=o.headers, json=payload).status_code == 200
    )
    entries = client.get(url + "/audit", headers=o.headers).json()
    scan = next(a for a in entries if a["action"] == "meal")["scans"][0]
    correction = {
        "operation_id": str(uuid4()),
        "kind": "void_scan",
        "code": code,
        "target": str(scan["id"]),
        "reason": "Scanned wrong badge",
    }
    assert (
        client.post(url + "/scan", headers=o.headers, json=correction).status_code
        == 200
    )
    assert (
        client.post(
            url + "/scan",
            headers=o.headers,
            json={**payload, "operation_id": str(uuid4())},
        ).status_code
        == 200
    )
    entries = client.get(url + "/audit", headers=o.headers).json()
    scans = [s for a in entries for s in a["scans"]]
    assert len(scans) == 2 and sum(s["voided"] for s in scans) == 1


def test_role_matrix_and_live_role_revocation(
    client, create_user, create_event, accept, engine
):
    superadmin, h, event, code, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    admin = create_user(role="admin")
    staff = create_user(role="lleidahacker")
    url = f"/v1/operations/{event}"
    for account in (superadmin, admin):
        assert client.get(url + "/manage", headers=account.headers).status_code == 200
    for account in (staff, h):
        assert client.get(url + "/manage", headers=account.headers).status_code == 403
        assert client.get(url + "/audit", headers=account.headers).status_code == 403
    assert client.get("/v1/user/all", headers=staff.headers).status_code == 403
    scanner = client.get(url + "/scanner", headers=staff.headers)
    assert scanner.status_code == 200, scanner.text
    assert scanner.json()["access_role"] == "lleidahacker"
    assert "teams" not in scanner.json()
    assert (
        client.post(
            url + "/scan",
            headers=staff.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": "meal",
                "code": code,
                "target": str(meal),
            },
        ).status_code
        == 200
    )
    for account in (staff, admin):
        assert (
            client.post(
                url + "/scan",
                headers=account.headers,
                json={
                    "operation_id": str(uuid4()),
                    "kind": "award",
                    "code": code,
                    "amount": 100,
                    "reason": "Unauthorized award",
                },
            ).status_code
            == 403
        )
        assert (
            client.patch(
                url + f"/staff/{staff.id}",
                headers=account.headers,
                json={"role": "superadmin", "reason": "Escalate"},
            ).status_code
            == 403
        )
    assert client.delete(f"/v1/event/{event}", headers=admin.headers).status_code == 403
    assert (
        client.put(
            f"/v1/event/{event}", headers=admin.headers, json={"price": 10}
        ).status_code
        == 403
    )
    config = client.get(url + "/manage", headers=admin.headers).json()
    config["title"] = "Updated by admin"
    assert (
        client.put(
            url + "/config",
            headers=admin.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Update title",
            },
        ).status_code
        == 200
    )
    config = client.get(url + "/manage", headers=admin.headers).json()
    config["prizes"] = [{"id": "free", "title": "Prize", "cost": 1, "stock": 100}]
    assert (
        client.put(
            url + "/config",
            headers=admin.headers,
            json={
                "version": config["version"],
                "config": config,
                "reason": "Change economy",
            },
        ).status_code
        == 403
    )
    assert (
        client.patch(
            url + f"/staff/{staff.id}",
            headers=superadmin.headers,
            json={"role": "admin", "reason": "Promote volunteer"},
        ).status_code
        == 200
    )
    assert client.get(url + "/manage", headers=staff.headers).status_code == 200
    assert (
        client.patch(
            url + f"/staff/{staff.id}",
            headers=superadmin.headers,
            json={"role": "lleidahacker", "reason": "End management shift"},
        ).status_code
        == 200
    )
    assert client.get(url + "/manage", headers=staff.headers).status_code == 403
    assert (
        client.get("/v1/auth/me", headers=staff.headers).json()["access_role"]
        == "lleidahacker"
    )
    assert (
        client.patch(
            url + f"/staff/{superadmin.id}",
            headers=superadmin.headers,
            json={"role": "admin", "reason": "Self demotion"},
        ).status_code
        == 409
    )


def test_legacy_job_title_cannot_escalate_access_role(client, create_user):
    staff = create_user(role="lleidahacker")
    response = client.put(
        f"/v1/lleidahacker/{staff.id}",
        headers=staff.headers,
        json={"role": "superadmin", "access_role": "superadmin", "is_admin": True},
    )
    assert response.status_code == 200, response.text
    me = client.get("/v1/auth/me", headers=staff.headers).json()
    assert me["access_role"] == "lleidahacker"


def test_global_role_assignment_preserves_participant_and_rechecks_session(
    client, create_user, create_event, accept, engine
):
    owner, participant, event, _code, _meal = prepare(
        client, create_user, create_event, accept, engine
    )
    admin = create_user(role="admin")
    endpoint = f"/v1/access/users/{participant.id}"
    before = client.get(f"/v1/hacker/{participant.id}", headers=owner.headers).json()
    for unauthorized in (admin, participant):
        response = client.patch(
            endpoint + "/role",
            headers=unauthorized.headers,
            json={"role": "superadmin", "reason": "Unauthorized escalation"},
        )
        assert response.status_code == 403
        assert (
            client.get(endpoint + "/history", headers=unauthorized.headers).status_code
            == 403
        )
    for role in ("admin", "superadmin", "lleidahacker", "hacker"):
        response = client.patch(
            endpoint + "/role",
            headers=owner.headers,
            json={"role": role, "reason": "Assign event responsibility"},
        )
        assert response.status_code == 200, response.text
        me = client.get("/v1/auth/me", headers=participant.headers).json()
        assert me["access_role"] == role
        assert me["type"] == "hacker"
        assert client.get(
            f"/v1/operations/{event}/manage", headers=participant.headers
        ).status_code == (200 if role in {"admin", "superadmin"} else 403)
    after = client.get(f"/v1/hacker/{participant.id}", headers=owner.headers).json()
    assert before == after
    history = client.get(endpoint + "/history", headers=owner.headers).json()
    assert len(history) == 4
    assert {row["actor_id"] for row in history} == {owner.id}
    assert history[0]["previous_role"] == "lleidahacker"
    assert history[0]["new_role"] == "hacker"
    assert (
        client.patch(
            f"/v1/access/users/{owner.id}/role",
            headers=owner.headers,
            json={"role": "hacker", "reason": "Self demotion"},
        ).status_code
        == 409
    )


def test_public_leaderboard_ranks_aliases_and_isolates_events(
    client, create_user, create_event, accept, engine
):
    from sqlalchemy import text

    owner = create_user(role="organizer")
    users = [create_user(nickname=nickname) for nickname in ("zeta", "alpha", "third")]
    event = create_event(users)
    base = f"/v1/operations/{event}"
    assert client.get(base + "/public").json()["leaderboard"] == []
    for user, amount in zip(users, (20, 20, 5), strict=True):
        accept(owner, event, user)
        code = user_code(engine, user)
        client.put(f"/v1/event/{event}/participate/{code}", headers=owner.headers)
        response = client.post(
            base + "/scan",
            headers=owner.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": "award",
                "code": code,
                "amount": amount,
                "reason": "Leaderboard verification",
            },
        )
        assert response.status_code == 200, response.text
    ranking = client.get(base + "/public").json()["leaderboard"]
    assert ranking == [
        {"rank": 1, "nickname": "alpha", "balance": 20},
        {"rank": 1, "nickname": "zeta", "balance": 20},
        {"rank": 3, "nickname": "third", "balance": 5},
    ]
    other_event = create_event([])
    assert (
        client.get(f"/v1/operations/{other_event}/public").json()["leaderboard"] == []
    )
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE my_user SET is_deleted=true WHERE id=:id"), {"id": users[0].id}
        )
        connection.execute(
            text("UPDATE hacker SET banned=true WHERE user_id=:id"), {"id": users[2].id}
        )
    assert client.get(base + "/public").json()["leaderboard"] == [
        {"rank": 1, "nickname": "alpha", "balance": 20}
    ]
