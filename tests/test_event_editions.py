# ruff: noqa: DTZ001 - fixed naive dates match database fixtures
from datetime import datetime


def test_year_lookup_never_returns_an_older_edition(client, create_event):
    create_event(
        name="HackEPS 2025",
        start_date=datetime(2025, 11, 22),
        end_date=datetime(2025, 11, 23),
    )
    assert client.get("/v1/event/get_hackeps/2026").status_code == 404
    current = create_event(
        name="HackEPS 2026",
        start_date=datetime(2026, 11, 28),
        end_date=datetime(2026, 11, 29),
    )
    assert client.get("/v1/event/get_hackeps/2026").json()["id"] == current


def test_sponsor_tier_is_independent_per_edition(client, create_event, create_user):
    organizer = create_user(role="organizer")
    hacker = create_user()
    company = client.post(
        "/v1/company/",
        headers=organizer.headers,
        json={
            "name": "Edition sponsor",
            "description": "",
            "website": "https://example.test",
            "tier": 1,
            "address": "",
            "linkdin": "",
            "telephone": "600000009",
        },
    ).json()["id"]
    old, current = create_event(), create_event()
    for event in [old, current]:
        response = client.put(
            f"/v1/event/{event}/sponsors/{company}", headers=organizer.headers
        )
        assert response.status_code == 200, response.text
    path = f"/v1/event/{current}/sponsors/{company}"
    assert client.patch(path, headers=hacker.headers, json={"tier": 2}).status_code in (
        401,
        403,
    )
    response = client.patch(
        path, headers=organizer.headers, json={"tier": 2, "display_order": 5}
    )
    assert response.status_code == 200, response.text
    assert client.get(f"/v1/event/{old}/sponsors").json()[0]["tier"] == 1
    assert client.get(f"/v1/event/{current}/sponsors").json()[0]["tier"] == 2
    assert client.get(f"/v1/company/{company}").json()["tier"] == 1
    assert (
        client.patch(path, headers=organizer.headers, json={"tier": 9}).status_code
        == 422
    )


def test_edition_programme_can_be_updated_without_changing_other_years(
    client, create_event, create_user
):
    organizer = create_user(role="organizer")
    event = create_event(
        name="HackEPS 2026",
        start_date=datetime(2026, 11, 28),
        end_date=datetime(2026, 11, 29),
    )
    programme = {
        "schedule": [
            {
                "title": "Opening",
                "description": "Welcome",
                "starts_at": "2026-11-28T09:00:00+01:00",
            }
        ],
        "activities": ["Workshop"],
    }
    response = client.put(
        f"/v1/event/{event}", headers=organizer.headers, json=programme
    )
    assert response.status_code == 200, response.text
    edition = client.get("/v1/event/get_hackeps/2026").json()
    assert edition["schedule"] == programme["schedule"]
    assert edition["activities"] == ["Workshop"]
