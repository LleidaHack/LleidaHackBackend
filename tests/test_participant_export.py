from datetime import UTC, datetime

from sqlalchemy.orm import Session


def test_export_preserves_statuses_and_effective_event_meals(
    client, create_user, create_event, engine
):
    from src.impl.Event.model import (
        HackerAccepted,
        HackerParticipation,
        HackerRegistration,
        HackerRejected,
    )
    from src.impl.Meal.model import HackerMeal, Meal
    from src.impl.Operations.model import ScanRecord

    admin = create_user(role="admin")
    users = [create_user(name=f"Export {i}") for i in range(4)]
    event = create_event(users)
    other = create_event(users)
    with Session(engine) as session:
        session.add(HackerAccepted(event_id=event, user_id=users[0].id))
        session.add(HackerRejected(event_id=event, user_id=users[1].id))
        session.get(
            HackerRegistration, (users[2].id, event)
        ).cancelled_at = datetime.now(UTC).replace(tzinfo=None)
        reg = session.get(HackerRegistration, (users[0].id, event))
        reg.confirmed_assistance = True
        reg.food_restrictions = "Sense gluten"
        reg.cv = "private-pdf-data"
        session.add(HackerParticipation(event_id=event, user_id=users[1].id))
        session.add(HackerParticipation(event_id=other, user_id=users[0].id))
        meals = [
            Meal(event_id=e, name="Dinar", description="")
            for e in (event, event, other)
        ]
        session.add_all(meals)
        session.flush()
        meal_ids = [meal.id for meal in meals]
        session.add(HackerMeal(user_id=users[0].id, meal_id=meal_ids[0]))
        session.add(HackerMeal(user_id=users[3].id, meal_id=meal_ids[2]))
        for user, meal, round_number, voided, event_id in [
            (0, 0, 1, False, event),
            (0, 0, 2, False, event),
            (1, 1, 1, False, event),
            (2, 1, 1, True, event),
            (3, 2, 1, False, other),
        ]:
            session.add(
                ScanRecord(
                    event_id=event_id,
                    user_id=users[user].id,
                    kind="meal",
                    target=str(meal_ids[meal]),
                    round=round_number,
                    voided=voided,
                )
            )
        session.commit()
    response = client.get(
        f"/v1/operations/{event}/participants-export", headers=admin.headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert [meal["id"] for meal in data["meals"]] == meal_ids[:2]
    rows = data["participants"]
    assert [row["status"] for row in rows] == [
        "accepted",
        "rejected",
        "cancelled",
        "pending",
    ]
    assert [row["checked_in"] for row in rows] == [False, True, False, False]
    assert [row["eaten_meal_ids"] for row in rows] == [
        [meal_ids[0]],
        [meal_ids[1]],
        [],
        [],
    ]
    assert rows[0]["confirmed_assistance"] is True
    assert rows[0]["food_restrictions"] == "Sense gluten"
    assert rows[0]["has_cv"] is True
    assert "private-pdf-data" not in response.text
    assert "confirm_assistance_token" not in response.text


def test_export_requires_management_and_handles_empty_or_missing_events(
    client, create_user, create_event
):
    event = create_event()
    path = f"/v1/operations/{event}/participants-export"
    assert client.get(path).status_code in (401, 403)
    for role in ("hacker", "lleidahacker"):
        assert (
            client.get(path, headers=create_user(role=role).headers).status_code == 403
        )
    for role in ("admin", "superadmin"):
        admin = create_user(role=role)
        response = client.get(path, headers=admin.headers)
        assert response.status_code == 200, response.text
        assert response.json() == {"meals": [], "participants": []}
        assert (
            client.get(
                "/v1/operations/999999/participants-export", headers=admin.headers
            ).status_code
            == 404
        )
