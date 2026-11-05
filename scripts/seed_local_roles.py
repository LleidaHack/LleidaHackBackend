"""Provision role-specific demo accounts only in the isolated local database."""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

url = make_url(os.environ["DATABASE__URL"])
if url.host not in {"localhost", "127.0.0.1"} or url.database != "llh_operations_dev":
    raise SystemExit("This script only supports the local demonstration database")
from src import imports  # noqa: F401
from src.impl.LleidaHacker.model import LleidaHacker
from src.impl.UserConfig.model import UserConfig
from src.utils.security import get_password_hash
from src.utils.Token import AccesToken, RefreshToken, ResetPassToken, VerificationToken

with Session(create_engine(url)) as session:
    organizer = (
        session.query(LleidaHacker).filter_by(email="organizer@example.test").one()
    )
    organizer.access_role = "superadmin"
    for index, role in enumerate(("admin", "lleidahacker"), start=20):
        email = f"{role}@example.test"
        user = session.query(LleidaHacker).filter_by(email=email).first()
        if not user:
            config = UserConfig(default_lang="ca")
            session.add(config)
            session.flush()
            user = LleidaHacker(
                name=f"Local {role}",
                nickname=f"demo-{role}",
                email=email,
                telephone=f"600{index:06d}",
                password=get_password_hash("LocalDemo2026!"),
                birthdate=date(2000, 1, 1),
                food_restrictions="",
                address="",
                shirt_size="M",
                code=f"DEMO{index:03d}",
                config_id=config.id,
                is_verified=True,
                github="",
                linkedin="",
                role="organizer",
                nif=f"LOCAL-{role}",
                active=True,
                accepted=True,
                access_role=role,
            )
            session.add(user)
            session.flush()
            user.token = AccesToken(user).to_token()
            user.refresh_token = RefreshToken(user).to_token()
            user.verification_token = VerificationToken(user).to_token()
            user.rest_password_token = ResetPassToken(user).to_token()
        else:
            user.access_role = role
    session.commit()
print(
    "Local roles: organizer@example.test (superadmin), admin@example.test, lleidahacker@example.test"
)
