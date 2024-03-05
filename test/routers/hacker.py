from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from schemas.Hacker import Hacker as SchemaHacker
from database import Base
from database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
import random
import string
import base64

SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_password(length):
    letters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str[0].upper() + result_str[1:]


def test_create_rnd_hacker():
    return SchemaHacker(name="test",
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


# ===== signup endpoint test =====
async def mock_add_hacker():
    return {"id": 1}


def mock_create_all_tokens():
    return "fake_access_token", "fake_refresh_token"


@patch("services.hacker.add_hacker", new=mock_add_hacker)
@patch("security.create_all_tokens", new=mock_create_all_tokens)
def test_hacker_signup():
    payload = test_create_rnd_hacker()
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
    expected_response_body = [{
        "id": 1,
        "name": "Hacker1"
    }, {
        "id": 2,
        "name": "Hacker2"
    }]
    assert response.json() == expected_response_body


# ===== get_hacker endpoint test =====
async def mock_get_hacker(hacker_id):
    return {"id": hacker_id, "name": "TestHacker"}


@patch("services.hacker.get_hacker", new=mock_get_hacker)
@patch("routers.hacker.get_hacker.JWTBearer", new=mock_jwt_bearer)
def test_get_hacker():
    response = client.get("/1")
    assert response.status_code == 200
    expected_response_body = {"id": 1, "name": "TestHacker"}
    assert response.json() == expected_response_body


# ===== update_hacker endpoint test =====
async def mock_update_hacker(hacker_id):
    return MagicMock(hacker_id), True


@patch("services.hacker.update_hacker", new=mock_update_hacker)
@patch("routers.hacker.update_hacker.JWTBearer", new=mock_jwt_bearer)
def test_update_hacker():
    response = client.put("/1", json={"name": "UpdatedHacker"})
    assert response.status_code == 200
    expected_response_body = {
        "success": True,
        "updated_id": 1,
        "updated": True
    }
    assert response.json() == expected_response_body


# ===== ban_hacker endpoint test =====
async def mock_ban_hacker(user_id):
    return MagicMock(user_id)


@patch("services.hacker.ban_hacker", new=mock_ban_hacker)
@patch("routers.hacker.ban_hacker.JWTBearer", new=mock_jwt_bearer)
def test_ban_hacker():
    response = client.post("/1/ban")
    assert response.status_code == 200
    expected_response_body = {"success": True, "banned_id": 1}
    assert response.json() == expected_response_body


# ===== unban_hacker endpoint test =====
async def mock_unban_hacker(user_id):
    return MagicMock(user_id)


@patch("services.hacker.unban_hacker", new=mock_unban_hacker)
@patch("routers.hacker.unban_hacker.JWTBearer", new=mock_jwt_bearer)
def test_unban_hacker():
    response = client.post("/1/unban")
    assert response.status_code == 200
    expected_response_body = {"success": True, "unbanned_id": 1}
    assert response.json() == expected_response_body


# ===== delete_hacker endpoint test =====
async def mock_remove_hacker():
    return test_create_rnd_hacker()


@patch("services.hacker.remove_hacker", new=mock_remove_hacker())
@patch("routers.hacker.delete_hacker", new=mock_jwt_bearer)
def test_delete_hacker():
    response = client.delete("/1/")
    assert response.status_code == 200
    expected_response_body = {"success": True, "deleted_id": 1}
    assert response.json() == expected_response_body


# ===== get_hacker_events endpoint test =====
async def mock_get_hacker_events():
    return {"success": True, "expected_id": 1}


@patch("services.hacker.get_hacker_events", new=mock_get_hacker_events)
def test_get_hacker_events():
    response = client.get("/1/events")
    assert response.status_code == 200
    expected_response_body = {"success": True, "expected_id": 1}
    assert response.json() == expected_response_body
