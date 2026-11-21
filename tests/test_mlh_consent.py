import pytest
from sqlalchemy.orm import Session


@pytest.mark.parametrize("consent", [False, None, "true", 1, "missing"])
def test_signup_requires_explicit_mlh_consent(client, engine, signup_payload, consent):
    from src.impl.User.model import User

    if consent == "missing":
        signup_payload["config"].pop("mlh_code_of_conduct")
    else:
        signup_payload["config"]["mlh_code_of_conduct"] = consent
    response = client.post("/v1/hacker/signup", json=signup_payload)
    assert response.status_code == 422, response.text
    with Session(engine) as session:
        assert session.query(User).filter_by(email=signup_payload["email"]).first() is None


def test_signup_persists_and_returns_mlh_consent(client, engine, signup_payload):
    from src.impl.User.model import User

    response = client.post("/v1/hacker/signup", json=signup_payload)
    assert response.status_code == 200, response.text
    signup = response.json()
    with Session(engine) as session:
        user = session.get(User, signup["user_id"])
        assert user.config.mlh_code_of_conduct is True
    profile = client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {signup['access_token']}"}
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["config"]["mlh_code_of_conduct"] is True


def test_existing_users_are_not_assumed_to_have_accepted(engine, create_user):
    from src.impl.User.model import User

    user = create_user()
    with Session(engine) as session:
        assert session.get(User, user.id).config.mlh_code_of_conduct is False
