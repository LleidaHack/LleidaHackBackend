from sqlalchemy.orm import Session


def test_company_without_image_and_event_list(
    client, create_user, create_event, engine
):
    from src.impl.Company.model import Company
    from src.impl.Event.model import Event

    organizer = create_user(role="organizer")
    response = client.post(
        "/v1/company/",
        headers=organizer.headers,
        json={
            "name": "Company",
            "description": "",
            "website": "https://example.test",
            "tier": 1,
            "address": "",
            "linkdin": "",
            "telephone": "600000009",
        },
    )
    assert response.status_code == 200, response.text
    company_id = response.json()["id"]
    response = client.get(f"/v1/company/{company_id}")
    assert response.status_code == 200, response.text
    assert response.json()["image"] is None
    response = client.get(f"/v1/company/{company_id}/events", headers=organizer.headers)
    assert response.status_code == 200, response.text
    assert response.json() == []
    event_id = create_event()
    with Session(engine) as session:
        company = session.get(Company, company_id)
        company.events.append(session.get(Event, event_id))
        session.commit()
    response = client.get(f"/v1/company/{company_id}/events", headers=organizer.headers)
    assert response.status_code == 200, response.text
    assert [event["id"] for event in response.json()] == [event_id]
    hacker = create_user()
    path = f"/v1/event/{event_id}/sponsors/{company_id}"
    assert client.delete(path, headers=hacker.headers).status_code in (401, 403)
    response = client.delete(path, headers=organizer.headers)
    assert response.status_code == 200, response.text
    assert client.get(f"/v1/event/{event_id}/sponsors").json() == []
    assert client.delete(path, headers=organizer.headers).status_code == 400
    assert (
        client.delete(f"/v1/company/{company_id}", headers=hacker.headers).status_code
        == 403
    )
    response = client.delete(f"/v1/company/{company_id}", headers=organizer.headers)
    assert response.status_code == 200, response.text
    assert client.get(f"/v1/company/{company_id}").status_code == 404
