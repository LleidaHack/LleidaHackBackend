from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session


@pytest.mark.parametrize("token_name", ["refresh", "verification", "reset"])
def test_non_access_token_cannot_access_api(client, create_user, token_name):
    user = create_user()
    response = client.get("/v1/user/all", headers={"Authorization": f"Bearer {getattr(user, token_name)}"})
    assert response.status_code == 401


@pytest.mark.parametrize("token_name", ["access", "verification", "reset"])
def test_refresh_rejects_wrong_purpose(client, create_user, token_name):
    user = create_user()
    response = client.post("/v1/auth/refresh-token", headers={"Authorization": f"Bearer {getattr(user, token_name)}"})
    assert response.status_code == 401


@pytest.mark.parametrize("state", [{"banned": True}, {"is_verified": False}, {"is_deleted": True}])
def test_current_account_state_blocks_access_and_refresh(client, create_user, engine, state):
    from src.impl.User.model import User

    user = create_user()
    with Session(engine) as session:
        stored = session.get(User, user.id)
        for key, value in state.items():
            setattr(stored, key, value)
        session.commit()
    assert client.get("/v1/user/all", headers=user.headers).status_code == 401
    response = client.post("/v1/auth/refresh-token", headers={"Authorization": f"Bearer {user.refresh}"})
    assert response.status_code == 401


def test_inactive_organizer_cannot_use_refresh_for_privileges(client, create_user):
    user = create_user(role="organizer", active=False)
    response = client.get("/v1/user/all", headers={"Authorization": f"Bearer {user.refresh}"})
    assert response.status_code == 401
    assert client.get("/v1/user/all", headers=user.headers).status_code == 401
    assert client.get("/v1/auth/login", auth=(user.email, "TestPassword123")).status_code == 401


def test_login_replaces_old_tokens(client, create_user):
    user = create_user()
    response = client.get("/v1/auth/login", auth=(user.email, "TestPassword123"))
    assert response.status_code == 200, response.text
    assert client.get("/v1/user/all", headers=user.headers).status_code == 401
    new_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/v1/user/all", headers=new_headers).status_code == 200


def test_concurrent_refresh_only_succeeds_once(client, create_user):
    user = create_user()
    headers = {"Authorization": f"Bearer {user.refresh}"}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post("/v1/auth/refresh-token", headers=headers), range(2)))
    assert sum(response.status_code == 200 for response in results) == 1
    assert all(response.status_code in (200, 400, 401) for response in results)
    assert client.get("/v1/user/all", headers=user.headers).status_code == 401


def test_ban_then_unban_does_not_restore_old_session(client, create_user):
    organizer = create_user(role="organizer")
    user = create_user()
    for action in ("ban", "unban"):
        response = client.post(f"/v1/hacker/{user.id}/{action}", headers=organizer.headers)
        assert response.status_code == 200, response.text
    assert client.get("/v1/user/all", headers=user.headers).status_code == 401
    assert client.post("/v1/auth/refresh-token", headers={"Authorization": f"Bearer {user.refresh}"}).status_code == 401


@pytest.mark.parametrize("change", [
    {"type": "unknown"}, {"user_id": None}, {"expt": "invalid"},
    {"expt": datetime.now().isoformat()},
    {"expt": (datetime.now(UTC) - timedelta(days=1)).isoformat()},
])
def test_invalid_claims_return_authentication_error(client, create_user, change):
    from src.utils.Token import BaseToken

    user = create_user()
    claims = BaseToken.decode(user.access)
    claims.update(change)
    token = BaseToken.encode(claims)
    response = client.get("/v1/user/all", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert token not in response.text


def test_verification_token_is_single_use(client, create_user):
    user = create_user(is_verified=False)
    response = client.post("/v1/auth/verify", params={"token": user.verification})
    assert response.status_code == 200, response.text
    assert client.post("/v1/auth/verify", params={"token": user.verification}).status_code == 401


def test_service_token_is_rejected_for_personal_flows(client):
    from src.configuration.Settings import settings

    headers = {"Authorization": f"Bearer {settings.security.service_token}"}
    assert client.get("/v1/auth/me", headers=headers).status_code == 401
    assert client.post("/v1/auth/refresh-token", headers=headers).status_code == 401
