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
