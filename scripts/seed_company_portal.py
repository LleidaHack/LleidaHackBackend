"""Add a shared company account to the isolated operations demo; never send mail."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.impl.Company.model import Company
from src.impl.CompanyPortal.model import PortalAccount, PortalGrant
from src.impl.Event.model import Event
from src.impl.Operations.model import EventOperations
from src.utils.security import get_password_hash

url = make_url(os.environ["DATABASE__URL"])
if url.host not in {"localhost", "127.0.0.1"} or url.database != "llh_operations_dev":
    raise SystemExit("Seed only supports the local llh_operations_dev database")
with Session(create_engine(url)) as session:
    event = session.query(Event).filter_by(name="HackEPS Local Demo").one()
    config = session.get(EventOperations, event.id)
    rooms = [room["id"] for room in config.config["rooms"]]
    account = (
        session.query(PortalAccount).filter_by(email="company@example.test").first()
    )
    if not account:
        company = Company(name="Local Demo Company")
        session.add(company)
        session.flush()
        account = PortalAccount(
            company_id=company.id,
            email="company@example.test",
            password_hash=get_password_hash("LocalDemo2026!"),
        )
        session.add(account)
        session.flush()
    grant = (
        session.query(PortalGrant)
        .filter_by(account_id=account.id, event_id=event.id)
        .first()
    )
    if not grant:
        session.add(PortalGrant(account_id=account.id, event_id=event.id, rooms=rooms))
    session.commit()
    print(
        "Local company account ready at /companies. No mail was sent; existing notes were preserved."
    )
