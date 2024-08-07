import base64
import random
import string

import pytest
from fastapi.testclient import TestClient

from main import app
from src.impl.User.model import User as ModelUser
from src.impl.User.schema import User as SchemaUser

client = TestClient(app)


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_password(length):
    letters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str[0].upper() + result_str[1:]


@pytest.fixture
def user_id_and_token():
    response = client.post(
        "/user/",
        data=SchemaUser(name="test",
                        nickname=random_string(10),
                        password=random_password(10),
                        birthdate="2000-01-01",
                        food_restrictions="None",
                        email=random_string(5) + "@test.com",
                        telephone="".join(
                            [str(random.randint(0, 9)) for _ in range(10)]),
                        address="test",
                        shirt_size="M",
                        image=base64.b64encode(b'test').decode('utf-8'),
                        is_image_url=False))
    assert response.status_code == 200
    return response.json()["user_id"], response.json()["token"]


def test_get_users(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get("/user/all",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_user(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get(f"/user/{user_id}",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_user_by_email(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get(f"/user/email/{email}",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == email


def test_get_user_by_nickname(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get(f"/user/nickname/{nickname}",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["nickname"] == nickname


def test_get_user_by_phone(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get(f"/user/phone/{phone}",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["telephone"] == phone


def test_get_user_by_code(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.get(f"/user/code/{code}",
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["code"] == code


def test_update_user(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.put(
        f"/user/{user_id}",
        data=SchemaUser(name="test",
                        nickname=random_string(10),
                        password=random_password(10),
                        birthdate="2000-01-01",
                        food_restrictions="None",
                        email=random_string(5) + "@test.com",
                        telephone="".join(
                            [str(random.randint(0, 9)) for _ in range(10)]),
                        address="test",
                        shirt_size="M",
                        image=base64.b64encode(b'test').decode('utf-8'),
                        is_image_url=False),
        headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_delete_user(user_id_and_token):
    user_id, token = user_id_and_token
    response = client.delete(f"/user/{user_id}",
                             headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == user_id
