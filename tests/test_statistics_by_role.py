# ruff: noqa: F811
from uuid import uuid4

from tests.test_event_operations import prepare
from tests.test_tickets_vouchers import accept, add_activity  # noqa: F401


def test_statistics_split_hackers_mentors_and_guests(
    client, create_user, create_event, accept, engine
):
    admin, hacker, event, hacker_badge, meal = prepare(
        client, create_user, create_event, accept, engine
    )
    base = f"/v1/operations/{event}"
    mentor = client.post(
        base + "/mentors",
        headers=admin.headers,
        json={"name": "Mentor", "email": "mentor@example.test"},
    ).json()["id"]
    guest = client.post(
        base + "/guests",
        headers=admin.headers,
        json={"name": "Guest", "email": "guest@example.test"},
    ).json()["id"]
    company = client.post(
        base + "/guests",
        headers=admin.headers,
        json={"name": "Rep", "email": "rep@example.test", "kind": "empresa"},
    ).json()["id"]
    inactive = client.post(
        base + "/guests",
        headers=admin.headers,
        json={"name": "Gone", "email": "gone@example.test"},
    ).json()["id"]
    assert (
        client.patch(
            base + f"/guests/{inactive}", headers=admin.headers, json={"active": False}
        ).status_code
        == 200
    )
    mentor_badge = client.post(
        f"/v1/event/{event}/vouchers/generate", headers=admin.headers, json={"count": 1}
    ).json()["vouchers"][0]["code"]
    assert (
        client.put(
            base + f"/mentors/{mentor}/badge",
            headers=admin.headers,
            json={"code": mentor_badge},
        ).status_code
        == 200
    )
    activity = add_activity(client, admin, event)

    def scan(badge, kind, target):
        response = client.post(
            base + "/scan",
            headers=admin.headers,
            json={
                "operation_id": str(uuid4()),
                "kind": kind,
                "code": badge,
                "target": target,
                "round": 1,
            },
        )
        assert response.status_code == 200, response.text

    scan(hacker_badge, "meal", str(meal))
    scan(hacker_badge, "activity", activity)
    scan(mentor_badge, "meal", str(meal))

    url = f"/v1/event/{event}/statistics_participants"
    # Without the flag the response keeps its hacker-only shape.
    legacy = client.get(url, headers=admin.headers).json()
    assert [row["id"] for row in legacy] == [hacker.id]
    assert "role" not in legacy[0]

    response = client.get(url + "?by_role=true", headers=admin.headers)
    assert response.status_code == 200, response.text
    rows = {row["id"]: row for row in response.json()}
    assert set(rows) == {hacker.id, mentor, guest, company}
    assert {i: r["role"] for i, r in rows.items()} == {
        hacker.id: "hacker",
        mentor: "mentor",
        guest: "convidat",
        company: "empresa",
    }
    hacker_row = rows[hacker.id]
    assert (hacker_row["checked_in"], hacker_row["meals"]) == (True, 1)
    assert hacker_row["activities"] == 1
    assert rows[mentor]["checked_in"] and rows[mentor]["meals"] == 1
    assert rows[mentor]["email"] == "mentor@example.test"
    assert rows[mentor]["confirmed_assistance"] is True
    assert not rows[guest]["checked_in"] and rows[guest]["meals"] == 0
    assert rows[company]["location"] is None
    assert client.get(url + "?by_role=true", headers=hacker.headers).status_code in (
        401,
        403,
    )
