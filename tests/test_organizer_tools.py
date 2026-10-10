def test_notes_are_private_to_organizers(client, create_user, create_event):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    path = f"/v1/event/{event_id}/notes/{hacker.id}"

    created = client.post(path, json={"body": "Good CV"}, headers=organizer.headers)
    assert created.status_code == 200, created.text
    assert created.json()["author_id"] == organizer.id

    listed = client.get(path, headers=organizer.headers)
    assert [n["body"] for n in listed.json()] == ["Good CV"]
    participants = client.get(
        f"/v1/event/{event_id}/hackers_participants_list", headers=organizer.headers
    ).json()["participants"]
    assert participants[0]["notes_count"] == 1

    assert client.get(path, headers=hacker.headers).status_code == 401
    assert (
        client.post(path, json={"body": "x"}, headers=hacker.headers).status_code == 401
    )

    note_id = created.json()["id"]
    deleted = client.delete(
        f"/v1/event/{event_id}/notes/item/{note_id}", headers=organizer.headers
    )
    assert deleted.status_code == 200, deleted.text
    assert client.get(path, headers=organizer.headers).json() == []


def test_note_requires_registration_and_text(client, create_user, create_event):
    organizer, outsider = create_user(role="organizer"), create_user()
    event_id = create_event([])
    path = f"/v1/event/{event_id}/notes/{outsider.id}"
    assert (
        client.post(path, json={"body": "x"}, headers=organizer.headers).status_code
        >= 400
    )
    assert (
        client.post(path, json={"body": ""}, headers=organizer.headers).status_code
        == 422
    )


def test_status_changes_are_audited(client, create_user, create_event):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    rejected = client.put(
        f"/v1/event/{event_id}/reject/{hacker.id}", headers=organizer.headers
    )
    assert rejected.status_code == 200, rejected.text

    log = client.get(f"/v1/event/{event_id}/audit", headers=organizer.headers)
    assert log.status_code == 200, log.text
    entry = log.json()[0]
    assert (entry["action"], entry["actor_id"], entry["target_id"]) == (
        "reject",
        organizer.id,
        hacker.id,
    )
    assert (
        client.get(f"/v1/event/{event_id}/audit", headers=hacker.headers).status_code
        == 401
    )


def test_participants_list_includes_registration_fields(
    client, create_user, create_event
):
    organizer, hacker = create_user(role="organizer"), create_user()
    event_id = create_event([hacker])
    participant = client.get(
        f"/v1/event/{event_id}/hackers_participants_list", headers=organizer.headers
    ).json()["participants"][0]
    assert {"study_center", "cv", "registered_at", "notes_count"} <= participant.keys()
