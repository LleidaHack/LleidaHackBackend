from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session


def assert_no_credentials(value):
    forbidden = {"password", "token", "refresh_token", "verification_token", "rest_password_token"}
    if isinstance(value, dict):
        assert not forbidden.intersection(value)
        for item in value.values():
            assert_no_credentials(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_credentials(item)


def test_pending_profile_does_not_expose_verification_token(client, signup_payload):
    signup = client.post("/v1/hacker/signup", json=signup_payload).json()
    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {signup['access_token']}"})
    assert response.status_code == 200, response.text
    assert response.json()["is_verified"] is False
    assert response.json()["email"] == signup_payload["email"]
    assert_no_credentials(response.json())


def test_verification_response_has_no_credentials(client, signup_payload, engine):
    from src.impl.User.model import User

    signup = client.post("/v1/hacker/signup", json=signup_payload).json()
    with Session(engine) as session:
        token = session.get(User, signup["user_id"]).verification_token
    response = client.post("/v1/auth/verify", params={"token": token})
    assert response.status_code == 200, response.text
    assert response.json() == {"success": True}
    assert_no_credentials(response.json())


def test_hacker_cannot_read_organizer_nif(client, signup_payload, engine):
    from src.impl.LleidaHacker.model import LleidaHacker

    signup = client.post("/v1/hacker/signup", json=signup_payload).json()
    with Session(engine) as session:
        organizer = LleidaHacker(
            name="Organizer", nickname="organizer", email="organizer@example.test",
            telephone="600000002", birthdate=date(2000, 1, 1), role="organizer",
            nif="synthetic-nif", github="", linkedin="", code="organizer-code",
        )
        session.add(organizer)
        session.commit()
        organizer_id = organizer.id
    from src.impl.User.model import User
    with Session(engine) as session:
        user = session.get(User, signup["user_id"])
        user.is_verified = True
        session.commit()
    headers = {"Authorization": f"Bearer {signup['access_token']}"}
    for path in ("/v1/lleidahacker/all", f"/v1/lleidahacker/{organizer_id}"):
        response = client.get(path, headers=headers)
        assert response.status_code == 200, response.text
        assert "synthetic-nif" not in response.text
        assert '"nif"' not in response.text


@pytest.mark.parametrize("value", ["", "secret", "HOLA", " " * 32, "your-" + "example" * 8])
def test_insecure_secrets_are_rejected(client, value):
    from src.configuration.Settings import SecuritySettings

    for field in ("secret_key", "service_token"):
        with pytest.raises(ValidationError):
            SecuritySettings(_env_file=None, **{field: value})


def test_missing_secrets_are_rejected(client, monkeypatch):
    from src.configuration.Settings import SecuritySettings

    monkeypatch.delenv("SECURITY__SECRET_KEY")
    monkeypatch.delenv("SECURITY__SERVICE_TOKEN")
    with pytest.raises(ValidationError):
        SecuritySettings(_env_file=None)


def test_invalid_jwt_does_not_leak_token_or_traceback(client):
    token = "malformed-sensitive-token"
    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert token not in response.text
    assert "Traceback" not in response.text


def test_application_disables_debug(app):
    assert app.debug is False


def test_event_groups_do_not_expose_invitation_codes(client, create_user, create_event, create_group):
    owner, outsider = create_user(), create_user()
    event_id = create_event([owner, outsider])
    group = create_group(event_id, [owner])
    response = client.get(f"/v1/event/{event_id}/groups", headers=outsider.headers)
    assert response.status_code == 200, response.text
    assert group.code not in response.text
    assert_no_credentials(response.json())


def test_pending_hackers_response_filters_credentials(client, create_user, create_event):
    from src.configuration.Settings import settings

    user = create_user()
    event_id = create_event([user])
    response = client.get(f"/v1/event/{event_id}/pending",
                          headers={"Authorization": f"Bearer {settings.security.service_token}"})
    assert response.status_code == 200, response.text
    assert response.json()["hackers"][0]["id"] == user.id
    assert_no_credentials(response.json())


def test_public_organizer_groups_filter_nested_credentials_and_nif(client, create_user, engine):
    from src.impl.LleidaHackerGroup.model import LleidaHackerGroup, LleidaHackerGroupUser
    from src.impl.User.model import User

    organizer = create_user(role="organizer")
    with Session(engine) as session:
        user = session.get(User, organizer.id)
        group = LleidaHackerGroup(name="Organizers", description="", image="", leaders=[user])
        session.add(group)
        session.flush()
        session.add(LleidaHackerGroupUser(group_id=group.id, user_id=user.id, primary=True))
        session.commit()
    response = client.put("/v1/lleidahacker/group/sorted/")
    assert response.status_code == 200, response.text
    assert response.json()["llhk_groups"][0]["members"]
    assert '"nif"' not in response.text
    assert_no_credentials(response.json())


def test_accept_group_returns_filtered_event(client, create_user, create_event, create_group):
    organizer = create_user(role="organizer")
    member = create_user()
    event_id = create_event([member])
    group = create_group(event_id, [member])
    response = client.put(f"/v1/event/{event_id}/acceptgroup/{group.id}", headers=organizer.headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == event_id
    assert_no_credentials(response.json())
