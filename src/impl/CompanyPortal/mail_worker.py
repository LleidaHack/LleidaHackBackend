"""Deliver durable invitations once; uncertain sends require a new invitation."""

import logging
import time

from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src import imports  # noqa: F401
from src.configuration.Settings import settings
from src.impl.CompanyPortal.model import PortalAccount, PortalInvitation
from src.impl.CompanyPortal.router import now
from src.impl.Mail.client import MailClient

logger = logging.getLogger(__name__)


def deliver_one(engine, client):
    with Session(engine) as session:
        row = (
            session.query(PortalInvitation)
            .filter(PortalInvitation.delivery_state.in_(["pending", "ready"]))
            .order_by(PortalInvitation.id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if not row:
            return False
        if row.consumed or row.expires_at <= now() or not row.delivery_url:
            row.delivery_state = "expired"
            row.delivery_url = None
            session.commit()
            return True
        account = session.get(PortalAccount, row.account_id)
        invitation_id, email, url, mail_id = (
            row.id,
            account.email,
            row.delivery_url,
            row.mail_id,
        )
        row.delivery_state = "creating" if mail_id is None else "sending"
        session.commit()
    try:
        if mail_id is None:
            template = client.get_template_by_name("company_portal_invitation")
            if not template or not getattr(template, "id", None):
                raise RuntimeError("Company invitation template is missing")
            mail = client.create_mail(
                MailCreate(
                    template_id=template.id,
                    subject="HackEPS · Accés al portal d’empreses",
                    fields=url,
                    receiver_mail=email,
                )
            )
            mail_id = mail.id
            with Session(engine) as session:
                row = session.get(PortalInvitation, invitation_id)
                row.mail_id = mail_id
                row.delivery_state = "ready"
                session.commit()
            return True
        response = client.send_mail_by_id(mail_id)
        status = "sent" if 200 <= int(response.status_code) < 300 else "uncertain"
    except Exception:  # noqa: BLE001 -- isolate delivery failures without exposing tokens  # Do not log recipient, setup URL or upstream exception payloads.
        status = "uncertain"
        logger.warning(
            "Company invitation delivery requires review: id=%s", invitation_id
        )
    with Session(engine) as session:
        row = session.get(PortalInvitation, invitation_id)
        row.delivery_state = status
        row.delivery_url = None
        session.commit()
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = create_engine(settings.database.url, pool_pre_ping=True)
    client = MailClient()
    while True:
        try:
            if deliver_one(engine, client):
                continue
        except Exception:  # noqa: BLE001 -- isolate delivery failures without exposing tokens
            logger.warning("Company invitation worker unavailable; retrying later")
        time.sleep(2)
