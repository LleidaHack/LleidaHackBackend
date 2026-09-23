from sqlalchemy.orm import Session


def test_signup_without_optional_fields_can_read_profile(client, engine):
    from src.impl.User.model import User

    response = client.post(
        "/v1/hacker/signup",
        json={
            "name": "Minimal User",
            "nickname": "minimal-user",
            "email": "minimal@example.test",
            "password": "TestPassword123",
            "telephone": "600000022",
            "birthdate": "2000-01-01",
            "config": {
                "default_lang": "en",
                "recive_notifications": False,
                "comercial_notifications": False,
                "terms_and_conditions": True,
            },
        },
    )
    assert response.status_code == 200, response.text
    user_id = response.json()["user_id"]
    with Session(engine) as session:
        verification = session.get(User, user_id).verification_token
    assert (
        client.post("/v1/auth/verify", params={"token": verification}).status_code
        == 200
    )
    response = client.get(
        "/v1/auth/login", auth=("minimal@example.test", "TestPassword123")
    )
    assert response.status_code == 200, response.text
    headers = {"Authorization": "Bearer " + response.json()["access_token"]}
    response = client.get(f"/v1/hacker/{user_id}", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["address"] is None
    assert response.json()["food_restrictions"] is None
    assert "password" not in response.json()
