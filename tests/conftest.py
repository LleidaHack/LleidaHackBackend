import os
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
    raise RuntimeError("Tests require a disposable database with a name ending in _test")

os.environ.update(
    ENV="main",
    DATABASE__URL=TEST_DATABASE_URL,
    SECURITY__SECRET_KEY="test-signing-key-not-for-production-123456",
    SECURITY__SERVICE_TOKEN="test-service-key-not-for-production-123456",
    CLIENTS__MAIL_CLIENT__URL="http://mail.invalid/",
)


@pytest.fixture(scope="session")
def app():
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
    from alembic import command
    from alembic.config import Config

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")


@pytest.fixture(autouse=True)
def clean_database(engine, database):
    with engine.begin() as connection:
        tables = connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
            "AND tablename != 'alembic_version'"
        )).scalars().all()
        quoted = ", ".join(engine.dialect.identifier_preparer.quote(t) for t in tables)
        if quoted:
            connection.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(app, monkeypatch):
    from src.impl.Mail.client import MailClient

    monkeypatch.setattr(MailClient, "create_mail", lambda self, mail: SimpleNamespace(id=1))
    monkeypatch.setattr(MailClient, "send_mail_by_id", lambda self, mail_id: None)
    monkeypatch.setattr(MailClient, "get_internall_template_id", lambda self, template: 1)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def signup_payload():
    return {
        "name": "Test Hacker", "nickname": "test-hacker",
        "password": "TestPassword123", "birthdate": "2000-01-01",
        "email": "hacker@example.test", "telephone": "600000001",
        "food_restrictions": "", "address": "", "shirt_size": "M",
        "github": "", "linkedin": "", "study_center": "", "location": "",
        "how_did_you_meet_us": "", "cv": "",
        "config": {
            "recive_notifications": True, "default_lang": "en",
            "comercial_notifications": False, "terms_and_conditions": True,
        },
    }
