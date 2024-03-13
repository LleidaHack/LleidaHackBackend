from fastapi.testclient import TestClient
from database import Base
from database import get_db
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
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

schema_hacker = {"name": "test",
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


def test_signup():
    response = client.post("/hacker/signup", json=schema_hacker)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "test@email.com"
