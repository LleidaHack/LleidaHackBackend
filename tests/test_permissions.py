import pytest
from sqlalchemy.orm import Session


@pytest.mark.parametrize("action", ["remove", "leader", "update", "delete", "add"])
def test_outsider_cannot_change_group(
    client, create_user, create_event, create_group, engine, action
):
    from src.impl.HackerGroup.model import HackerGroup

    leader, member, outsider = create_user(), create_user(), create_user()
    event_id = create_event([leader, member, outsider])
    group = create_group(event_id, [leader, member])
    base = f"/v1/hacker/group/{group.id}"
    requests = {
        "remove": ("DELETE", f"{base}/members/{member.id}", None),
        "leader": ("PUT", f"{base}/leader/{outsider.id}", None),
        "update": ("PUT", base, {"leader_id": outsider.id}),
        "delete": ("DELETE", base, None),
        "add": ("POST", f"{base}/members/{outsider.id}", None),
    }
    method, path, payload = requests[action]
    response = client.request(method, path, json=payload, headers=outsider.headers)
    assert response.status_code == 403, response.text
    with Session(engine) as session:
        stored = session.get(HackerGroup, group.id)
        assert stored.leader_id == leader.id
        assert {user.id for user in stored.members} == {leader.id, member.id}


def test_leader_can_transfer_only_to_a_member(
    client, create_user, create_event, create_group
):
    leader, member, outsider = create_user(), create_user(), create_user()
    event_id = create_event([leader, member, outsider])
    group = create_group(event_id, [leader, member])
    path = f"/v1/hacker/group/{group.id}"
    assert (
        client.put(f"{path}/leader/{outsider.id}", headers=leader.headers).status_code
        == 400
    )
    assert (
        client.put(
            path, json={"leader_id": outsider.id}, headers=leader.headers
        ).status_code
        == 400
    )
    assert (
        client.put(f"{path}/leader/{member.id}", headers=member.headers).status_code
        == 403
    )
    assert (
        client.put(f"{path}/leader/{member.id}", headers=leader.headers).status_code
        == 200
    )


def test_members_can_leave_and_empty_group_is_deleted(
    client, create_user, create_event, create_group, engine
):
    from src.impl.HackerGroup.model import HackerGroup

    leader, member = create_user(), create_user()
    group = create_group(create_event([leader, member]), [leader, member])
    for user in (leader, member):
        response = client.delete(
            f"/v1/hacker/group/{group.id}/members/{user.id}", headers=user.headers
        )
        assert response.status_code == 200, response.text
    with Session(engine) as session:
        assert session.get(HackerGroup, group.id) is None


def test_join_requires_own_identity_and_valid_capacity(
    client, create_user, create_event, create_group
):
    leader, outsider, other = create_user(), create_user(), create_user()
    event_id = create_event([leader, outsider, other], max_group_size=2)
    group = create_group(event_id, [leader])
    base = f"/v1/hacker/group/{group.code}/members_by_code"
    assert (
        client.post(f"{base}/{other.id}", headers=outsider.headers).status_code == 403
    )
    assert (
        client.post(f"{base}/{outsider.id}", headers=outsider.headers).status_code
        == 200
    )
    assert (
        client.post(f"{base}/{outsider.id}", headers=outsider.headers).status_code
        == 400
    )
    assert client.post(f"{base}/{other.id}", headers=other.headers).status_code == 400


def test_group_creator_cannot_choose_another_leader(client, create_user, create_event):
    actor, other = create_user(), create_user()
    payload = {
        "name": "Team",
        "description": "",
        "leader_id": other.id,
        "event_id": create_event([actor, other]),
    }
    assert (
        client.post(
            "/v1/hacker/group/", json=payload, headers=actor.headers
        ).status_code
        == 403
    )
    payload["leader_id"] = actor.id
    assert (
        client.post(
            "/v1/hacker/group/", json=payload, headers=actor.headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/hacker/group/", json=payload, headers=actor.headers
        ).status_code
        == 400
    )


def test_organizer_can_manage_groups(client, create_user, create_event, create_group):
    organizer = create_user(role="organizer")
    leader, member = create_user(), create_user()
    group = create_group(create_event([leader, member]), [leader])
    base = f"/v1/hacker/group/{group.id}"
    assert (
        client.post(
            f"{base}/members/{member.id}", headers=organizer.headers
        ).status_code
        == 200
    )
    assert (
        client.put(
            base, json={"name": "Updated"}, headers=organizer.headers
        ).status_code
        == 200
    )
    assert client.delete(base, headers=organizer.headers).status_code == 200


def test_company_signup_requires_organizer_and_cannot_self_transfer(
    client, create_user, signup_payload, engine
):
    from src.impl.Company.model import Company
    from src.impl.User.model import User

    with Session(engine) as session:
        companies = [Company(name="First"), Company(name="Second")]
        session.add_all(companies)
        session.commit()
        first, second = [company.id for company in companies]
    payload = {
        **signup_payload,
        "telephone": "699999999",
        "company_id": first,
        "role": "member",
        "active": 1,
    }
    actor = create_user()
    assert client.post("/v1/company-user/signup", json=payload).status_code == 401
    assert (
        client.post(
            "/v1/company-user/signup", json=payload, headers=actor.headers
        ).status_code
        == 403
    )
    organizer = create_user(role="organizer")
    response = client.post(
        "/v1/company-user/signup", json=payload, headers=organizer.headers
    )
    assert response.status_code == 200, response.text
    credentials = response.json()
    with Session(engine) as session:
        user = session.get(User, credentials["user_id"])
        user.is_verified = True
        session.commit()
    headers = {"Authorization": f"Bearer {credentials['access_token']}"}
    response = client.put(
        f"/v1/company-user/{credentials['user_id']}",
        json={"company_id": second},
        headers=headers,
    )
    assert response.status_code == 422
    response = client.post(
        f"/v1/company/{second}/users/{credentials['user_id']}", headers=headers
    )
    assert response.status_code == 403
    response = client.post(
        f"/v1/company/{second}/users/{credentials['user_id']}",
        headers=organizer.headers,
    )
    assert response.status_code == 200, response.text
    with Session(engine) as session:
        user = session.get(User, credentials["user_id"])
        assert user.company_id == second
        assert user.token == ""
