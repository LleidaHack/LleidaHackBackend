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
