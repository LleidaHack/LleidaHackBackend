from unittest.mock import patch
from fastapi.testclient import TestClient
from schemas.Hacker import Hacker as SchemaHacker
from database import db_get
from main import app
import random
import string
import base64

client = TestClient(app)


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_password(length):
    letters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str[0].upper() + result_str[1:]


# ===== signup endpoint test =====
async def mock_add_hacker():
    return {"id": 1}


def mock_create_all_tokens():
    return "fake_access_token", "fake_refresh_token"


@patch("services.hacker.add_hacker", new=mock_add_hacker)
@patch("security.create_all_tokens", new=mock_create_all_tokens)
def test_hacker_signup():
    payload = {
        SchemaHacker(name="test",
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
                     is_image_url=False,
                     recive_mails=True,
                     github="string",
                     linkedin="string")
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 200
    expected_response_body = {
        "success": True,
        "user_id": 1,
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token"
    }
    assert response.json() == expected_response_body


# ===== get_all endpoint test =====
async def mock_get_all():
    return [{"id": 1, "name": "Hacker1"}, {"id": 2, "name": "Hacker2"}]


def mock_jwt_bearer():
    return "fake_token"


@patch("services.hacker.get_all", new=mock_get_all)
@patch("routers.hacker.get_hackers.JWTBearer", new=mock_jwt_bearer)
def test_get_hackers():
    response = client.get("/all")
    assert response.status_code == 200
    expected_response_body = [{"id": 1, "name": "Hacker1"}, {"id": 2, "name": "Hacker2"}]
    assert response.json() == expected_response_body
