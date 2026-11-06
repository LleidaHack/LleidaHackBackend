# ruff: noqa: F811
from uuid import uuid4

from tests.test_event_operations import prepare
from tests.test_tickets_vouchers import accept, user_code  # noqa: F401


def test_ticket_rejected_and_admin_recovery_preserves_meal_history(
    client, create_user, create_event, accept, engine
):
    admin, user, event, badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    staff = create_user(role="lleidahacker")
    base = f"/v1/operations/{event}"
    ticket = user_code(engine, user)

    def scan(code, kind="meal", target=None):
        return client.post(
            base + "/scan",
            headers=staff.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": kind,
                "code": code,
                "target": str(meal) if target is None else target,
            },
        )

    for kind in ("meal", "activity", "redeem"):
        assert scan(ticket, kind).status_code == 422
    assert (
        client.put(f"/v1/meal/{meal}/eat/{ticket}", headers=staff.headers).status_code
        != 200
    )
    assert scan(badge).status_code == 200
    vouchers = client.post(
        f"/v1/event/{event}/vouchers/generate", headers=admin.headers, json={"count": 2}
    ).json()["vouchers"]
    new = vouchers[0]["code"]
    assert scan(new).status_code == 404
    endpoint = f"/v1/event/{event}/vouchers/{new}/replace/{ticket}"
    for actor in (staff, user):
        assert client.put(endpoint, headers=actor.headers).status_code in (401, 403)
    # A failed replacement must leave the original working and linked.
    assert (
        client.put(
            f"/v1/event/{event}/vouchers/VZZZZZZZZ/replace/{ticket}",
            headers=admin.headers,
        ).status_code
        == 404
    )
    assert scan(badge).status_code == 409
    assert client.put(endpoint, headers=admin.headers).status_code == 200
    assert scan(badge).status_code == 404
    assert scan(new).status_code == 409
    assert (
        client.put(
            f"/v1/event/{event}/vouchers/{badge}/assign/{ticket}", headers=admin.headers
        ).status_code
        == 400
    )
    assert (
        client.post(
            base + f"/meals/{meal}/round",
            headers=admin.headers,
            json={"expected_round": 1, "action": "next", "reason": "Second meal round"},
        ).status_code
        == 200
    )
    response = client.post(
        base + "/scan",
        headers=staff.headers,
        json={
            "operation_id": str(uuid4()),
            "kind": "meal",
            "code": new,
            "target": str(meal),
            "round": 2,
        },
    )
    assert response.status_code == 200, response.text
    entries = client.get(base + "/audit", headers=admin.headers).json()
    replacement = next(e for e in entries if e["action"] == "badge.replace")
    assert replacement["actor_id"] == admin.id and replacement["user_id"] == user.id
    assert replacement["details"]["previous_voucher_id"]
