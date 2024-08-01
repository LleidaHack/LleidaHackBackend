import base64
from unittest.mock import MagicMock, patch

from database import Base, get_db
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app

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
    "github": "test",
    "linkedin": "test"
}

mock_new_hacker = MagicMock()
mock_new_hacker.id = 1
mock_access_token = "fake_access_token"
mock_refresh_token = "fake_refresh_token"