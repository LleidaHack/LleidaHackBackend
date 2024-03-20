from fastapi.testclient import TestClient
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
    "linkedin": "test"
}

mock_new_hacker = MagicMock()
mock_new_hacker.id = 1
mock_access_token = "fake_access_token"
mock_refresh_token = "fake_refresh_token"


@patch("services.hacker.add_hacker", return_value=mock_new_hacker)
@patch("security.create_all_tokens",
       return_value=(mock_access_token, mock_refresh_token))
@patch("services.mail.send_registration_confirmation_email")
def test_signup(mock_send_email, mock_create_tokens, mock_add_hacker):
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

    mock_add_hacker.assert_called_once_with(schema_hacker, fake_db)
    mock_create_tokens.assert_called_once_with(mock_new_hacker,
                                               fake_db,
                                               verification=True)
    mock_send_email.assert_called_once_with(mock_new_hacker)
