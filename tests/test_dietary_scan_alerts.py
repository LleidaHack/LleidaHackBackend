# ruff: noqa: F811
from uuid import uuid4

from sqlalchemy import text

from tests.test_event_operations import prepare
from tests.test_tickets_vouchers import accept  # noqa: F401


def test_dietary_information_is_event_scoped_and_replayed(
    client, create_user, create_event, accept, engine
):
    admin, user, event, badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE hacker_event_registration SET food_restrictions = :value WHERE event_id = :event AND user_id = :user"
            ),
            {"value": "Lactosa i fruits secs", "event": event, "user": user.id},
        )
    approved = client.get(
        f"/v1/event/{event}/get_approved_hackers", headers=admin.headers
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()[0]["food_restrictions"] == "Lactosa i fruits secs"
    light = client.get(
        f"/v1/event/{event}/statistics_participants", headers=admin.headers
    )
    assert light.status_code == 200, light.text
    assert light.json()[0]["food_restrictions"] == "Lactosa i fruits secs"
    assert set(light.json()[0]) == {
        "id",
        "name",
        "nickname",
        "email",
        "location",
        "studies",
        "study_center",
        "how_did_you_meet_us",
        "food_restrictions",
        "confirmed_assistance",
    }
    assert client.get(
        f"/v1/event/{event}/statistics_participants", headers=user.headers
    ).status_code in (401, 403)
    body = {
        "operation_id": str(uuid4()),
        "kind": "meal",
        "code": badge,
        "target": str(meal),
    }
    endpoint = f"/v1/operations/{event}/scan"
    assert client.post(endpoint, headers=user.headers, json=body).status_code == 403
    body["operation_id"] = str(uuid4())
    first = client.post(endpoint, headers=admin.headers, json=body)
    assert first.status_code == 200, first.text
    assert first.json()["food_restrictions"] == "Lactosa i fruits secs"
    assert (
        client.post(endpoint, headers=admin.headers, json=body).json() == first.json()
    )
    body["operation_id"] = str(uuid4())
    duplicate = client.post(endpoint, headers=admin.headers, json=body)
    assert duplicate.status_code == 409
    assert "food_restrictions" not in duplicate.json()


def test_manual_meal_preserves_event_response_and_includes_dietary_details(
    client, create_user, create_event, accept, engine
):
    admin, user, event, badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE hacker_event_registration SET food_restrictions = :value WHERE event_id = :event AND user_id = :user"
            ),
            {"value": "Gluten", "event": event, "user": user.id},
        )
    response = client.put(f"/v1/meal/{meal}/eat/{badge}", headers=admin.headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == event
    assert response.json()["food_restrictions"] == "Gluten"
    assert response.json()["participant"]


def test_voucher_reset_clears_consumption_and_is_replay_safe(
    client, create_user, create_event, accept, engine
):
    from sqlalchemy.orm import Session

    from src.impl.Operations.model import CoinMovement, EventOperations, OperationAudit

    admin, user, event, badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    scan = client.post(
        f"/v1/operations/{event}/scan",
        headers=admin.headers,
        json={
            "operation_id": str(uuid4()),
            "kind": "meal",
            "code": badge,
            "target": str(meal),
        },
    )
    assert scan.status_code == 200, scan.text
    with Session(engine) as session:
        log = OperationAudit(
            event_id=event,
            user_id=user.id,
            actor_id=admin.id,
            action="award",
            outcome="success",
            operation_id=str(uuid4()),
            details={},
            result={},
        )
        session.add(log)
        session.flush()
        session.add(
            CoinMovement(
                event_id=event,
                user_id=user.id,
                amount=50,
                balance_before=0,
                balance_after=50,
                reason="Test award",
                audit_id=log.id,
            )
        )
        redemption = OperationAudit(
            event_id=event,
            user_id=user.id,
            actor_id=admin.id,
            action="redeem",
            outcome="success",
            operation_id=str(uuid4()),
            details={"target": "test-prize"},
            result={},
        )
        session.add(redemption)
        session.flush()
        session.add(
            CoinMovement(
                event_id=event,
                user_id=user.id,
                amount=-10,
                balance_before=50,
                balance_after=40,
                reason="Test prize",
                audit_id=redemption.id,
            )
        )
        state = session.get(EventOperations, event)
        state.config = {
            **state.config,
            "prizes": [{"id": "test-prize", "title": "Test", "stock": 0, "cost": 10}],
        }
        session.commit()
    endpoint = f"/v1/event/{event}/vouchers/{badge}/reset"
    body = {
        "operation_id": str(uuid4()),
        "expected_hacker_id": user.id,
        "reason": "Reset test badge",
    }
    assert client.post(endpoint, headers=user.headers, json=body).status_code in (
        401,
        403,
    )
    response = client.post(endpoint, headers=admin.headers, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["voided_scans"] == 1
    assert response.json()["reversed_movements"] == 2
    with Session(engine) as session:
        assert session.get(EventOperations, event).config["prizes"][0]["stock"] == 1
    assert (
        client.post(endpoint, headers=admin.headers, json=body).json()
        == response.json()
    )
    voucher = client.get(
        f"/v1/event/{event}/vouchers/{badge}", headers=admin.headers
    ).json()
    assert voucher["hacker_id"] is None and voucher["revoked"] is False
    with engine.connect() as conn:
        assert (
            conn.execute(
                text(
                    "SELECT coalesce(sum(amount),0) FROM coin_movement WHERE event_id=:event AND user_id=:user"
                ),
                {"event": event, "user": user.id},
            ).scalar()
            == 0
        )
        assert (
            conn.execute(
                text(
                    "SELECT count(*) FROM hacker_meal WHERE meal_id=:meal AND user_id=:user"
                ),
                {"meal": meal, "user": user.id},
            ).scalar()
            == 0
        )
        assert (
            conn.execute(
                text(
                    "SELECT count(*) FROM hacker_event_registration WHERE event_id=:event AND user_id=:user"
                ),
                {"event": event, "user": user.id},
            ).scalar()
            == 1
        )
    body["operation_id"] = str(uuid4())
    assert client.post(endpoint, headers=admin.headers, json=body).status_code == 409


def test_catering_restrictions_require_acceptance_and_confirmation(
    client, create_user, create_event, accept, engine
):
    admin, user, event, _, _ = prepare(
        client, create_user, create_event, accept, engine
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE hacker_event_registration SET food_restrictions = 'Gluten', confirmed_assistance = false WHERE event_id = :event AND user_id = :user"
            ),
            {"event": event, "user": user.id},
        )
    endpoint = f"/v1/event/{event}/food_restrictions"
    assert client.get(endpoint, headers=admin.headers).json() == []
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE hacker_event_registration SET confirmed_assistance = true WHERE event_id = :event AND user_id = :user"
            ),
            {"event": event, "user": user.id},
        )
    response = client.get(endpoint, headers=admin.headers)
    assert response.status_code == 200
    assert response.json() == ["Gluten"]
    stats = client.get(
        f"/v1/event/{event}/statistics_participants", headers=admin.headers
    ).json()
    assert stats[0]["confirmed_assistance"] is True

    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM hacker_event_accepted WHERE event_id = :event AND user_id = :user"
            ),
            {"event": event, "user": user.id},
        )
    assert client.get(endpoint, headers=admin.headers).json() == []
