from fastapi.testclient import TestClient
import services.hacker
from models.TokenData import TokenData
from database import Base
from database import get_db
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
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

schema_hacker = {
    "name": "test",
    "nickname": "testNick",
    "password": "testPass1.",
    "birthdate": "2000-01-01",
    "food_restrictions": "None",
    "email": "test@email.com",
    "telephone": "000000000",
    "address": "test",
    "shirt_size": "M",
    "image": base64.b64encode(b'test').decode('utf-8'),
    "is_image_url": "False",
    "receive_mails": "True",
    "github": "test",
    "linkedin": "test",
    "studies": "string",
    "study_center": "string",
    "location": "string",
    "how_did_you_meet_us": "string",
    "cv": "string"
}

mock_access_token = "fake_access_token"
mock_refresh_token = "fake_refresh_token"


@patch("security.create_all_tokens",
       return_value=(mock_access_token, mock_refresh_token))
@patch("services.mail.send_registration_confirmation_email")
def test_signup(mock_send_email, mock_create_tokens):
    fake_db = MagicMock(TestingSessionLocal)
    response = client.post("/hacker/signup", json=schema_hacker)
    assert response.status_code == 200
    expected_response_body = {
        "success": True,
        "user_id": 1,
        "access_token": mock_access_token,
        "refresh_token": mock_refresh_token
    }
    assert response.json() == expected_response_body
    new_hacker = services.hacker.get_hacker(1, TestingSessionLocal, TokenData)
    mock_create_tokens.assert_called_once_with(new_hacker,
                                               fake_db,
                                               verification=True)
    mock_send_email.assert_called_once_with(new_hacker)


def test_get_hackers():
    response = client.get("/hacker/all")
    assert response.status_code == 200
    assert response.json() == "test"


def test_get_hacker():
    response = client.get("/hacker/1")
    assert response.status_code == 200
    assert response.json() == "test"


def test_update_hacker():
    response = client.post("/hacker/1", json=schema_hacker)
    assert response.status_code == 200
    updated = services.hacker.get_hacker(1, TestingSessionLocal, TokenData)
    expected_response_body = {
        "success": True,
        "updated_id": updated.id,
        "updated": updated
    }
    assert response.json() == expected_response_body


def test_ban_hacker():
    response = client.post("/hacker/1/ban")
    assert response.status_code == 200
    hacker = services.hacker.get_hacker(1, TestingSessionLocal, TokenData)
    expected_response_body = {"success": True, "banned_id": hacker.id}
    assert response.json() == expected_response_body
