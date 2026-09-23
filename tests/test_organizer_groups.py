def test_organizer_group_lifecycle(client, create_user):
    leader = create_user(role="organizer")
    member = create_user(role="organizer")
    outsider = create_user(role="organizer")
    base = "/v1/lleidahacker/group"
    response = client.post(
        base + "/", json={"name": "Team", "description": ""}, headers=leader.headers
    )
    assert response.status_code == 200, response.text
    path = f"{base}/{response.json()['id']}"
    assert client.get(path, headers=leader.headers).status_code == 200
    assert client.get(base + "/all", headers=leader.headers).status_code == 200
    assert (
        client.post(f"{path}/members/{member.id}", headers=outsider.headers).status_code
        == 403
    )
    assert (
        client.post(f"{path}/members/{member.id}", headers=leader.headers).status_code
        == 200
    )
    assert (
        client.post(f"{path}/members/{member.id}", headers=leader.headers).status_code
        == 400
    )
    response = client.get(path + "/members", headers=leader.headers)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 2
    assert (
        client.post(f"{path}/leader/{member.id}", headers=leader.headers).status_code
        == 200
    )
    assert (
        client.delete(f"{path}/leader/{leader.id}", headers=member.headers).status_code
        == 200
    )
    assert (
        client.delete(f"{path}/leader/{member.id}", headers=member.headers).status_code
        == 400
    )
    assert (
        client.delete(f"{path}/members/{leader.id}", headers=member.headers).status_code
        == 200
    )
    assert client.delete(path, headers=outsider.headers).status_code == 403
    assert client.delete(path, headers=member.headers).status_code == 200
    assert client.get(path, headers=member.headers).status_code == 404
