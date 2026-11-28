def test_raffle_lifecycle(client, create_user):
    admin = create_user("admin").headers
    hacker = create_user().headers
    path = "/v1/raffles"
    assert client.get(path + "/manage").status_code == 401
    assert client.post(path, json={"name": "Test"}, headers=hacker).status_code == 403
    new = client.post(path, json={"name": "Sorteig de prova"}, headers=admin)
    assert new.status_code == 201
    raffle = f"{path}/{new.json()['id']}"
    entry = {
        "name": "Anna Garcia",
        "email": "Anna@example.org",
        "phone": "+34 600 000 000",
        "postal_code": "25001",
        "city": "Lleida",
    }
    assert client.post(raffle + "/entries", json=entry).status_code == 201
    entry["email"] = entry["email"].lower()
    assert client.post(raffle + "/entries", json=entry).status_code == 201

    def draw(count):
        return client.post(raffle + "/draw", headers=admin, json={"count": count})

    assert draw(2).status_code == 422
    entry["email"] = "segona@example.org"
    assert client.post(raffle + "/entries", json=entry).status_code == 201
    assert draw(2).status_code == 200
    result = client.get(path + "/manage", headers=admin).json()[0]
    assert result["entries"] == 2
    assert {w["email"] for w in result["winners"]} == {
        "anna@example.org",
        "segona@example.org",
    }
    assert draw(1).status_code == 409
    assert client.post(raffle + "/entries", json=entry).status_code == 409
    assert client.get(path).json()[0].keys() == {"id", "name", "theme", "drawn_at"}
