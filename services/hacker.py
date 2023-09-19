from datetime import datetime as date
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup
from models.Hacker import HackerGroupUser as ModelHackerGroupUser
from models.Event import HackerRegistration as ModelHackerRegistration
from models.Event import HackerParticipation as ModelHackerParticipation
from models.Event import HackerAccepted as ModelHackerAccepted
from models.TokenData import TokenData
from models.UserType import UserType

from schemas.Hacker import Hacker as SchemaHacker
from schemas.Hacker import HackerUpdate as SchemaHackerUpdate

from sqlalchemy.orm import Session

from security import get_password_hash
from utils.service_utils import set_existing_data, check_image, generate_user_code

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException

from utils.hide_utils import hacker_show_private
from utils.service_utils import check_user


async def get_all(db: Session):
    return db.query(ModelHacker).all()


async def get_hacker(hackerId: int, db: Session, data: TokenData):
    user = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if user is None:
        raise NotFoundException("Hacker not found")
    if data.is_admin or (
            data.available and
        (data.type == UserType.LLEIDAHACKER.value or
         (data.type == UserType.HACKER.value and data.user_id == hackerId))):
        hacker_show_private(user)
    return user


async def add_hacker(payload: SchemaHacker, db: Session):
    check_user(db, payload.email, payload.nickname)
    new_hacker = ModelHacker(**payload.dict(), code=generate_user_code(db))
    if payload.image is not None:
        payload = check_image(payload)
    new_hacker.password = get_password_hash(payload.password)

    db.add(new_hacker)
    db.commit()
    db.refresh(new_hacker)
    return new_hacker


async def remove_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and
                (data.type == UserType.LLEIDAHACKER.value or
                 (data.type == UserType.HACKER and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if not hacker:
        raise NotFoundException("Hacker not found")
    hacker_groups_ids = db.query(
        ModelHackerGroupUser).filter(ModelHackerGroupUser.hacker_id == hackerId).all()
    hacker_groups_ids = [group.group_id for group in hacker_groups_ids]
    hacker_groups = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id.in_(hacker_groups_ids)).all()
    for group in hacker_groups:
        if len(group.hackers) == 1:
            group.members.remove(hacker)
            db.delete(group)
        else:
            if group.leader_id == hackerId:
                members_ids = [h.id for h in group.hackers]
                members_ids.remove(hackerId)
                group.leader_id = members_ids[0]
            group.members.remove(hacker)
    event_regs = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hackerId).all()
    for event_reg in event_regs:
        db.delete(event_reg)
    event_parts = db.query(ModelHackerParticipation).filter(
        ModelHackerParticipation.user_id == hackerId).all()
    for event_part in event_parts:
        db.delete(event_part)
    event_accs = db.query(ModelHackerAccepted).filter(
        ModelHackerAccepted.user_id == hackerId).all()
    for event_acc in event_accs:
        db.delete(event_acc)
    db.delete(hacker)
    db.commit()
    return hacker


async def update_hacker(hackerId: int, payload: SchemaHackerUpdate,
                        db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    if payload.image is not None:
        payload = check_image(payload)
    updated = set_existing_data(hacker, payload)
    hacker.updated_at = date.now()
    updated.append("updated_at")
    if payload.password is not None:
        hacker.password = get_password_hash(payload.password)
    db.commit()
    db.refresh(hacker)
    return hacker, updated


async def ban_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    if hacker.banned:
        raise InvalidDataException("Hacker already banned")
    hacker.banned = 1
    db.commit()
    db.refresh(hacker)
    return hacker


async def unban_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    if not hacker.banned:
        raise InvalidDataException("Hacker already unbanned")
    hacker.banned = 0
    db.commit()
    db.refresh(hacker)
    return hacker


#TODO: #34 Check if token validation is correct
async def get_hacker_events(hackerId: int, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return hacker.events


#TODO: #34 Check if token validation is correct
async def get_hacker_groups(hackerId: int, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return hacker.groups
