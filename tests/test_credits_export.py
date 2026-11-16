from sqlalchemy.orm import Session


def test_credits_are_event_scoped_and_presentations_are_per_team(
    client, create_user, create_event, engine
):
    from src.impl.Event.model import HackerRegistration
    from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
    from src.impl.Operations.model import Presentation

    admin = create_user(role="admin")
    users = [create_user(name=f"Participant {i}") for i in range(5)]
    event = create_event(users)
    other = create_event(users)
    with Session(engine) as session:
        for user in users[:4]:
            session.get(HackerRegistration, (user.id, event)).wants_credit = True
        session.get(HackerRegistration, (users[4].id, other)).wants_credit = True
        for i, (event_id, member, states) in enumerate(
            [
                (event, users[0], ["done", "done"]),
                (event, users[1], ["waiting", "presenting", "skipped"]),
                (other, users[2], ["done"]),
                (event, users[4], ["done"]),
            ]
        ):
            group = HackerGroup(
                name=f"Team {i}",
                code=f"credits-{i}",
                description="",
                leader_id=member.id,
                event_id=event_id,
            )
            session.add(group)
            session.flush()
            session.add(HackerGroupUser(group_id=group.id, hacker_id=member.id))
            for j, state in enumerate(states):
                session.add(
                    Presentation(
                        event_id=event_id,
                        group_id=group.id,
                        room="room",
                        track=f"track-{j}",
                        state=state,
                    )
                )
        session.commit()
    response = client.get(f"/v1/operations/{event}/credits", headers=admin.headers)
    assert response.status_code == 200, response.text
    assert response.json() == [
        {"name": f"Participant {i}", "email": users[i].email, "team_presented": i == 0}
        for i in range(4)
    ]


def test_credits_require_management_access(client, create_user, create_event):
    event = create_event()
    path = f"/v1/operations/{event}/credits"
    assert client.get(path).status_code in (401, 403)
    for role in ("hacker", "lleidahacker"):
        assert (
            client.get(path, headers=create_user(role=role).headers).status_code == 403
        )
    for role in ("admin", "superadmin"):
        admin = create_user(role=role)
        response = client.get(path, headers=admin.headers)
        assert response.status_code == 200
        assert response.json() == []
        assert (
            client.get(
                "/v1/operations/999999/credits", headers=admin.headers
            ).status_code
            == 404
        )
