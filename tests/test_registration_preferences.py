from sqlalchemy.orm import Session


def test_registration_update_is_partial_and_allowed_at_capacity(client, create_user, create_event, engine):
    from src.impl.Event.model import HackerRegistration
    from src.impl.User.model import User

    user = create_user()
    event_id = create_event([user], max_participants=1)
    path = f"/v1/event/{event_id}/update-register/{user.id}"
    response = client.put(path, json={"shirt_size": "L"}, headers=user.headers)
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        assert registration.shirt_size == "L"
        assert registration.food_restrictions == ""
        assert session.get(User, user.id).shirt_size == "M"
    response = client.put(path, json={"shirt_size": "XL", "update_user": True}, headers=user.headers)
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        assert session.get(User, user.id).shirt_size == "XL"
        assert session.get(User, user.id).address == ""
    assert client.put(path, json={"shirt_size": "invalid"}, headers=user.headers).status_code == 422


def test_registration_update_does_not_change_another_user(client, create_user, create_event, engine):
    from src.impl.Event.model import HackerRegistration

    owner, outsider = create_user(), create_user()
    event_id = create_event([owner, outsider])
    response = client.put(f"/v1/event/{event_id}/update-register/{owner.id}",
                          json={"shirt_size": "XL"}, headers=outsider.headers)
    assert response.status_code in (401, 403)
    with Session(engine) as session:
        assert session.get(HackerRegistration, (owner.id, event_id)).shirt_size == "M"


def test_preferences_use_user_id_and_preserve_omitted_fields(client, create_user, engine):
    from src.impl.UserConfig.model import UserConfig
    from src.impl.User.model import User

    with Session(engine) as session:
        session.add(UserConfig(default_lang="ca"))
        session.commit()
    owner, outsider = create_user(), create_user()
    with Session(engine) as session:
        assert session.get(User, owner.id).config_id != owner.id
    path = f"/v1/userConfig/{owner.id}"
    before = client.get(path, headers=owner.headers)
    assert before.status_code == 200, before.text
    response = client.put(path, json={"default_lang": "es"}, headers=owner.headers)
    assert response.status_code == 200, response.text
    expected = {**before.json(), "default_lang": "es"}
    assert response.json() == expected
    assert client.put(path, json={"default_lang": "fr"}, headers=outsider.headers).status_code == 403
    assert client.get(path, headers=outsider.headers).status_code == 403
    assert client.get(path, headers=owner.headers).json() == expected
    assert client.put(path, json={"default_lang": None}, headers=owner.headers).status_code == 422


def test_missing_preferences_return_not_found(client, create_user):
    organizer = create_user(role="organizer")
    response = client.get("/v1/userConfig/9999", headers=organizer.headers)
    assert response.status_code == 404
