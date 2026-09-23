import pytest
from sqlalchemy.orm import Session


@pytest.mark.parametrize(
    "password", ["", "short", "lowercase123", "UPPERCASE123", "NoDigitsHere", None]
)
def test_password_policy_applies_to_reset_and_updates(client, create_user, password):
    user = create_user()
    assert (
        client.post(
            "/v1/auth/confirm-reset-password",
            json={"token": user.reset, "password": password},
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/v1/hacker/{user.id}", json={"password": password}, headers=user.headers
        ).status_code
        == 422
    )


def test_reset_uses_json_consumes_token_and_revokes_sessions(client, create_user):
    user = create_user()
    payload = {"token": user.reset, "password": "ChangedPassword123"}
    assert (
        client.post("/v1/auth/confirm-reset-password", params=payload).status_code
        == 422
    )
    response = client.post("/v1/auth/confirm-reset-password", json=payload)
    assert response.status_code == 200, response.text
    assert (
        client.post("/v1/auth/confirm-reset-password", json=payload).status_code == 401
    )
    assert client.get("/v1/auth/me", headers=user.headers).status_code == 401
    assert (
        client.post(
            "/v1/auth/refresh-token",
            headers={"Authorization": f"Bearer {user.refresh}"},
        ).status_code
        == 401
    )
    assert (
        client.get("/v1/auth/login", auth=(user.email, "TestPassword123")).status_code
        == 401
    )
    assert (
        client.get("/v1/auth/login", auth=(user.email, payload["password"])).status_code
        == 200
    )


def test_reset_request_does_not_revoke_existing_session(client, create_user, engine):
    from src.impl.User.model import User

    user = create_user()
    expected = client.post("/v1/auth/reset-password", params={"email": user.email})
    unknown = client.post(
        "/v1/auth/reset-password", params={"email": "missing@example.test"}
    )
    assert expected.status_code == unknown.status_code == 200
    assert expected.json() == unknown.json() == {"success": True}
    assert client.get("/v1/auth/me", headers=user.headers).status_code == 200
    with Session(engine) as session:
        stored = session.get(User, user.id)
        assert stored.token == user.access
        assert stored.refresh_token == user.refresh
        assert stored.rest_password_token != user.reset


def test_password_update_revokes_session(client, create_user):
    user = create_user()
    response = client.put(
        f"/v1/hacker/{user.id}",
        json={"password": "ChangedPassword123"},
        headers=user.headers,
    )
    assert response.status_code == 200, response.text
    assert client.get("/v1/auth/me", headers=user.headers).status_code == 401


def test_openapi_declares_reset_credentials_only_in_body(client):
    operation = client.get("/openapi.json").json()["paths"][
        "/v1/auth/confirm-reset-password"
    ]["post"]
    assert "application/json" in operation["requestBody"]["content"]
    assert not operation.get("parameters")
