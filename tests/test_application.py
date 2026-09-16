def test_openapi_is_available(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/v1/auth/login" in response.json()["paths"]


def test_signup_persists_user(client, signup_payload):
    response = client.post("/v1/hacker/signup", json=signup_payload)
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] > 0
