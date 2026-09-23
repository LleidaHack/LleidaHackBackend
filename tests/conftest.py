import os
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://audit_test:local-test-password@127.0.0.1:55439/lleidahack_test",
)
if not make_url(TEST_DATABASE_URL).database.endswith("_test"):
    raise RuntimeError(
        "Tests require a disposable database with a name ending in _test"
    )

os.environ.update(
    RATE_LIMIT__REDIS_URL=os.environ.get(
        "TEST_REDIS_URL", "redis://127.0.0.1:56379/15"
    ),
    RATE_LIMIT__PREFIX=f"lleidahack:test:{uuid.uuid4().hex}",
    RATE_LIMIT__ENABLED="true",
    ENV="main",
    DATABASE__URL=TEST_DATABASE_URL,
    SECURITY__SECRET_KEY="test-signing-key-not-for-production-123456",
    SECURITY__SERVICE_TOKEN="test-service-key-not-for-production-123456",
    CLIENTS__MAIL_CLIENT__URL="http://mail.invalid/",
)


@pytest.fixture(scope="session")
def app():
    # Register SQLAlchemy models through import side effects.
    from src import imports  # noqa: F401
    from src.impl.Mail.client import MailClient

    with patch.object(MailClient, "__init__", return_value=None):
        from main import app
    return app


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def database(engine):
    from alembic.config import Config

    from alembic import command

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")


@pytest.fixture(autouse=True)
def clean_database(engine, database):
    from redis import Redis

    with Redis.from_url(os.environ["RATE_LIMIT__REDIS_URL"]) as redis:
        keys = list(redis.scan_iter(match=os.environ["RATE_LIMIT__PREFIX"] + ":*"))
        if keys:
            redis.delete(*keys)
    with engine.begin() as connection:
        tables = (
            connection.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                    "AND tablename != 'alembic_version'"
                )
            )
            .scalars()
            .all()
        )
        quoted = ", ".join(engine.dialect.identifier_preparer.quote(t) for t in tables)
        if quoted:
            connection.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(app, monkeypatch):
    from src.impl.Mail.client import MailClient

    monkeypatch.setattr(
        MailClient, "create_mail", lambda self, mail: SimpleNamespace(id=1)
    )
    monkeypatch.setattr(MailClient, "send_mail_by_id", lambda self, mail_id: None)
    monkeypatch.setattr(
        MailClient, "get_internall_template_id", lambda self, template: 1
    )
    monkeypatch.setattr(MailClient, "ensure_initialized", lambda self: None)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def signup_payload():
    return {
        "name": "Test Hacker",
        "nickname": "test-hacker",
        "password": "TestPassword123",
        "birthdate": "2000-01-01",
        "email": "hacker@example.test",
        "telephone": "600000001",
        "food_restrictions": "",
        "address": "",
        "shirt_size": "M",
        "github": "",
        "linkedin": "",
        "study_center": "",
        "location": "",
        "how_did_you_meet_us": "",
        "cv": "",
        "config": {
            "recive_notifications": True,
            "default_lang": "en",
            "comercial_notifications": False,
            "terms_and_conditions": True,
        },
    }


@pytest.fixture
def create_user(app, engine):
    from datetime import date

    from sqlalchemy.orm import Session

    from src.impl.Hacker.model import Hacker
    from src.impl.LleidaHacker.model import LleidaHacker
    from src.impl.UserConfig.model import UserConfig
    from src.utils.security import get_password_hash
    from src.utils.Token import (
        AccesToken,
        RefreshToken,
        ResetPassToken,
        VerificationToken,
    )

    def create(role="hacker", **overrides):
        with Session(engine) as session:
            config = UserConfig(default_lang="en")
            session.add(config)
            session.flush()
            values = {
                "name": "Test User",
                "nickname": f"user-{config.id}",
                "email": f"user-{config.id}@example.test",
                "telephone": f"600{config.id:06d}",
                "password": get_password_hash("TestPassword123"),
                "birthdate": date(2000, 1, 1),
                "food_restrictions": "",
                "address": "",
                "shirt_size": "M",
                "code": f"code-{config.id}",
                "config_id": config.id,
                "is_verified": True,
                "github": "",
                "linkedin": "",
            }
            model = Hacker
            if role == "organizer":
                model = LleidaHacker
                values.update(
                    role="organizer",
                    nif=f"test-nif-{config.id}",
                    active=True,
                    accepted=True,
                )
            values.update(overrides)
            user = model(**values)
            session.add(user)
            session.flush()
            user.token = AccesToken(user).to_token()
            user.refresh_token = RefreshToken(user).to_token()
            user.verification_token = VerificationToken(user).to_token()
            user.rest_password_token = ResetPassToken(user).to_token()
            session.commit()
            return SimpleNamespace(
                id=user.id,
                email=user.email,
                access=user.token,
                refresh=user.refresh_token,
                verification=user.verification_token,
                reset=user.rest_password_token,
                headers={"Authorization": f"Bearer {user.token}"},
            )

    return create


@pytest.fixture
def create_event(app, engine):
    from sqlalchemy.orm import Session

    from src.impl.Event.model import Event, HackerRegistration

    def create(users=(), **overrides):
        with Session(engine) as session:
            values = {
                "name": "Test Event",
                "description": "",
                "location": "Test location",
                "max_participants": 100,
                "max_group_size": 4,
                "max_sponsors": 10,
                "archived": False,
                "is_open": True,
                "price": 0,
            }
            values.update(overrides)
            event = Event(**values)
            session.add(event)
            session.flush()
            for user in users:
                session.add(
                    HackerRegistration(
                        user_id=user.id,
                        event_id=event.id,
                        shirt_size="M",
                        food_restrictions="",
                    )
                )
            session.commit()
            return event.id

    return create


@pytest.fixture
def create_group(app, engine):
    from sqlalchemy.orm import Session

    from src.impl.HackerGroup.model import HackerGroup
    from src.impl.User.model import User

    def create(event_id, users):
        with Session(engine) as session:
            group = HackerGroup(
                name="Test Group",
                description="",
                leader_id=users[0].id,
                event_id=event_id,
                code=f"group-code-{users[0].id}",
                members=[session.get(User, user.id) for user in users],
            )
            session.add(group)
            session.commit()
            return SimpleNamespace(id=group.id, code=group.code)

    return create
