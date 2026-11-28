"""A hacker account must not be able to list or look up other participants."""

import pytest

OTHERS_ONLY = [
    "/v1/event/{event}/participants",
    "/v1/event/{event}/groups",
    "/v1/event/{event}/is_registered/{victim}",
    "/v1/event/{event}/is_accepted/{victim}",
    "/v1/event/{event}/has_confirmed/{victim}",
    "/v1/event/{event}/is_participant/{victim}",
    "/v1/hacker/all",
    "/v1/hacker/{victim}",
    "/v1/hacker/{victim}/events",
    "/v1/hacker/{victim}/groups",
    "/v1/hacker/group/all",
    "/v1/hacker/group/{group}",
    "/v1/hacker/group/{group}/members",
    "/v1/user/all",
    "/v1/user/{victim}",
]


@pytest.fixture
def scenario(create_user, create_event, create_group):
    attacker, victim, teammate = create_user(), create_user(), create_user()
    event = create_event([attacker, victim, teammate])
    group = create_group(event, [victim, teammate])
    return attacker, victim, event, group


def _url(path, victim, event, group):
    return path.format(event=event, victim=victim.id, group=group.id)


@pytest.mark.parametrize("path", OTHERS_ONLY)
def test_hacker_cannot_read_other_participants(client, scenario, path):
    attacker, victim, event, group = scenario
    response = client.get(_url(path, victim, event, group), headers=attacker.headers)
    assert response.status_code in (401, 403), response.text
    assert victim.email not in response.text


@pytest.mark.parametrize("path", OTHERS_ONLY)
def test_organizer_keeps_access(client, create_user, scenario, path):
    _, victim, event, group = scenario
    organizer = create_user(role="organizer")
    response = client.get(_url(path, victim, event, group), headers=organizer.headers)
    assert response.status_code == 200, response.text


def test_hacker_keeps_access_to_own_profile_flow(client, scenario):
    """Mirrors what the hackeps profile, login and team pages request."""
    _, victim, event, group = scenario
    own = victim.headers
    for path in (
        f"/v1/user/{victim.id}",
        f"/v1/hacker/{victim.id}",
        f"/v1/hacker/{victim.id}/events",
        f"/v1/hacker/{victim.id}/groups",
        f"/v1/hacker/group/{group.id}",
        f"/v1/hacker/group/{group.id}/members",
    ):
        response = client.get(path, headers=own)
        assert response.status_code == 200, (path, response.text)
    for check, expected in (
        ("is_registered", True),
        ("is_accepted", False),
        ("has_confirmed", False),
        ("is_participant", False),
    ):
        response = client.get(f"/v1/event/{event}/{check}/{victim.id}", headers=own)
        assert response.status_code == 200, (check, response.text)
        assert response.json() is expected
    team = client.get(f"/v1/hacker/group/{group.id}", headers=own).json()
    assert team["code"] == group.code
    profile = client.get(f"/v1/user/{victim.id}", headers=own).json()
    assert profile["type"] == "hacker" and profile["access_role"] == "hacker"
