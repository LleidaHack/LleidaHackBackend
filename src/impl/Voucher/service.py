import csv
import io
import re
import secrets
from datetime import datetime
from typing import Optional

from fastapi_sqlalchemy import db
from sqlalchemy.exc import IntegrityError

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.model import Event, HackerRegistration
from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.Voucher.model import Voucher
from src.utils.Base.BaseService import BaseService
from src.utils.Token import BaseToken
from src.utils.UserType import UserType

# Unambiguous alphabet (no 0/O/1/I) so a code can be typed by hand if the QR
# fails. No separators: the scanning app strips anything non-alphanumeric.
VOUCHER_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
VOUCHER_PREFIX = "V"
VOUCHER_LENGTH = 8
VOUCHER_PATTERN = re.compile(f"^{VOUCHER_PREFIX}[{VOUCHER_ALPHABET}]{{{VOUCHER_LENGTH}}}$")


def generate_voucher_code() -> str:
    return VOUCHER_PREFIX + "".join(
        secrets.choice(VOUCHER_ALPHABET) for _ in range(VOUCHER_LENGTH)
    )


class VoucherService(BaseService):
    name = "voucher_service"
    event_service: EventService = None
    hacker_service: HackerService = None

    def get_by_id(self, id: int) -> Voucher:
        voucher = db.session.query(Voucher).filter(Voucher.id == id).first()
        if voucher is None:
            raise NotFoundException("Voucher not found")
        return voucher

    def get_by_code(self, code: str, event_id: Optional[int] = None) -> Voucher:
        query = db.session.query(Voucher).filter(Voucher.code == code)
        if event_id is not None:
            query = query.filter(Voucher.event_id == event_id)
        voucher = query.first()
        if voucher is None:
            raise NotFoundException("Voucher not found")
        return voucher

    @staticmethod
    def is_voucher_code(code: str) -> bool:
        return VOUCHER_PATTERN.match(code) is not None

    def _event(self, event_id: int) -> Event:
        event = self.event_service.get_by_id(event_id)
        if event.archived:
            raise InvalidDataException(
                "Unable to operate with an archived event, unarchive it first"
            )
        return event

    @BaseService.needs_service(EventService)
    def generate(self, event_id: int, count: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self._event(event_id)
        existing = {
            code for (code,) in db.session.query(Voucher.code).all()
        }
        vouchers = []
        while len(vouchers) < count:
            code = generate_voucher_code()
            if code in existing:
                continue
            existing.add(code)
            vouchers.append(Voucher(event_id=event.id, code=code))
        db.session.add_all(vouchers)
        db.session.commit()
        for voucher in vouchers:
            db.session.refresh(voucher)
        return vouchers

    @BaseService.needs_service(EventService)
    def get_all(self, event_id: int, data: BaseToken, assigned: Optional[bool] = None):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        self.event_service.get_by_id(event_id)
        query = db.session.query(Voucher).filter(Voucher.event_id == event_id)
        if assigned is True:
            query = query.filter(Voucher.hacker_id.isnot(None))
        elif assigned is False:
            query = query.filter(Voucher.hacker_id.is_(None))
        return query.order_by(Voucher.id).all()

    @BaseService.needs_service(EventService)
    def get_summary(self, event_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        self.event_service.get_by_id(event_id)
        total = db.session.query(Voucher).filter(Voucher.event_id == event_id).count()
        assigned = (
            db.session.query(Voucher)
            .filter(Voucher.event_id == event_id, Voucher.hacker_id.isnot(None))
            .count()
        )
        return {"total": total, "assigned": assigned, "unassigned": total - assigned}

    def export_csv(self, event_id: int, data: BaseToken) -> str:
        vouchers = self.get_all(event_id, data)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["code", "hacker_id", "hacker_name", "assigned_at"])
        for voucher in vouchers:
            writer.writerow([
                voucher.code,
                voucher.hacker_id or "",
                voucher.hacker.name if voucher.hacker else "",
                voucher.assigned_at.isoformat() if voucher.assigned_at else "",
            ])
        return buffer.getvalue()

    @BaseService.needs_service(EventService)
    def get_voucher(self, event_id: int, code: str, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        self.event_service.get_by_id(event_id)
        return self.get_by_code(code, event_id)

    @BaseService.needs_service(EventService)
    @BaseService.needs_service(HackerService)
    def assign(self, event_id: int, voucher_code: str, hacker_code: str, data: BaseToken):
        """Check the hacker in and bind the physical voucher to them, atomically.

        Two scanning phones may race on the same voucher or the same hacker: the
        voucher row is locked and the (event, hacker) unique constraint rejects a
        second badge for the same person.
        """
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        event = self._event(event_id)
        if self.is_voucher_code(hacker_code):
            raise InvalidDataException(
                "Scanned a voucher instead of a ticket: scan the hacker's ticket QR"
            )
        if not self.is_voucher_code(voucher_code):
            raise InvalidDataException("Invalid voucher code")
        hacker = self.hacker_service.get_by_code(hacker_code)
        voucher = (
            db.session.query(Voucher)
            .filter(Voucher.code == voucher_code, Voucher.event_id == event.id)
            .with_for_update()
            .first()
        )
        if voucher is None:
            raise NotFoundException("Voucher not found for this event")
        if voucher.hacker_id is not None:
            if voucher.hacker_id == hacker.id:
                raise InvalidDataException("Voucher already assigned to this hacker")
            raise InvalidDataException("Voucher already assigned to another hacker")
        if hacker not in event.accepted_hackers:
            raise InvalidDataException("Hacker not accepted")
        registration = (
            db.session.query(HackerRegistration)
            .filter(
                HackerRegistration.user_id == hacker.id,
                HackerRegistration.event_id == event.id,
            )
            .first()
        )
        if registration is None:
            raise InvalidDataException("User not registered")
        current = (
            db.session.query(Voucher)
            .filter(Voucher.event_id == event.id, Voucher.hacker_id == hacker.id)
            .first()
        )
        if current is not None:
            raise InvalidDataException(
                f"Hacker already has voucher {current.code}"
            )
        message = ""
        if not registration.confirmed_assistance:
            registration.confirmed_assistance = True
            message = "user haven't confirmed so we forced confirmation"
        if hacker not in event.participants:
            event.participants.append(hacker)
        voucher.hacker_id = hacker.id
        voucher.assigned_at = datetime.now()
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise InvalidDataException("Hacker already has a voucher for this event")
        db.session.refresh(voucher)
        return {
            "success": True,
            "event_id": event.id,
            "voucher_code": voucher.code,
            "hacker_id": hacker.id,
            "hacker_name": hacker.name,
            "hacker_shirt_size": registration.shirt_size,
            "food_restrictions": registration.food_restrictions,
            "message": message,
        }

    @BaseService.needs_service(EventService)
    def unassign(self, event_id: int, voucher_code: str, data: BaseToken):
        """Free a voucher (lost/damaged badge). Participation is kept."""
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        self._event(event_id)
        voucher = self.get_by_code(voucher_code, event_id)
        if voucher.hacker_id is None:
            raise InvalidDataException("Voucher is not assigned")
        voucher.hacker_id = None
        voucher.assigned_at = None
        db.session.commit()
        db.session.refresh(voucher)
        return voucher
