import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_normal_application_never_exposes_local_verification(client):
    assert client.get("/v1/auth/local-verification").status_code == 404
    assert (
        client.post(
            "/v1/auth/local-verification", json={"email": "test@example.test"}
        ).status_code
        == 404
    )


def test_local_verification_checks_origin_and_enables_login(app, create_user):
    from App import App
    from install.local_verification import local_verification_router

    local = FastAPI()
    App(local).setup_all(logging.getLogger("local-verification-test"))
    local.include_router(local_verification_router())
    user = create_user(is_verified=False)
    with TestClient(
        local, base_url="http://localhost", client=("127.0.0.1", 1234)
    ) as client:
        assert client.get("/v1/auth/local-verification").json() == {"enabled": True}
        assert (
            client.post(
                "/v1/auth/local-verification",
                json={"email": user.email},
                headers={"Origin": "https://other.example"},
            ).status_code
            == 403
        )
        result = client.post(
            "/v1/auth/local-verification",
            json={"email": user.email},
            headers={"Origin": "http://localhost:3000"},
        )
        assert result.status_code == 200, result.text
        assert (
            client.get(
                "/v1/auth/login", auth=(user.email, "TestPassword123")
            ).status_code
            == 200
        )
    with TestClient(
        local, base_url="http://localhost", client=("192.0.2.1", 1234)
    ) as client:
        assert (
            client.post(
                "/v1/auth/local-verification", json={"email": user.email}
            ).status_code
            == 403
        )
