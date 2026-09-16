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


def test_assistance_token_is_scoped_to_one_confirmation(client, create_user, create_event, engine):
    from src.impl.Event.model import HackerRegistration, HackerAccepted
    from src.impl.User.model import User
    from src.utils.Token import AssistenceToken

    user = create_user()
    event_id = create_event([user])
    with Session(engine) as session:
        token = AssistenceToken(session.get(User, user.id), event_id).to_token()
        registration = session.get(HackerRegistration, (user.id, event_id))
        registration.confirm_assistance_token = token
        session.add(HackerAccepted(user_id=user.id, event_id=event_id))
        session.commit()
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/v1/user/all", headers=headers).status_code == 401
    assert client.post("/v1/auth/refresh-token", headers=headers).status_code == 401
    response = client.get("/v1/event/confirm_assistance/", headers=headers)
    assert response.status_code == 200, response.text
    assert client.get("/v1/event/confirm_assistance/", headers=headers).status_code == 401
    with Session(engine) as session:
        registration = session.get(HackerRegistration, (user.id, event_id))
        assert registration.confirmed_assistance is True
        assert registration.confirm_assistance_token == ""


def test_deactivation_revokes_organizer_session(client, create_user):
    administrator = create_user(role="organizer")
    target = create_user(role="organizer")
    for action in ("deactivate", "activate"):
        response = client.post(f"/v1/lleidahacker/{target.id}/{action}", headers=administrator.headers)
        assert response.status_code == 200, response.text
    assert client.get("/v1/user/all", headers=target.headers).status_code == 401
    assert client.post("/v1/auth/refresh-token", headers={"Authorization": f"Bearer {target.refresh}"}).status_code == 401


def test_unverified_login_has_specific_error_only_after_correct_password(client, create_user):
    user = create_user(is_verified=False)
    incorrect = client.get("/v1/auth/login", auth=(user.email, "wrong-password"))
    assert incorrect.status_code == 401
    assert "code" not in incorrect.json()
    pending = client.get("/v1/auth/login", auth=(user.email, "TestPassword123"))
    assert pending.status_code == 401
    assert pending.json()["code"] == "EMAIL_NOT_VERIFIED"
    assert "access_token" not in pending.json()
    assert client.post("/v1/auth/verify", params={"token": user.verification}).status_code == 200
    assert client.get("/v1/auth/login", auth=(user.email, "TestPassword123")).status_code == 200
