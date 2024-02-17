from datetime import datetime as date
from pydantic import parse_obj_as
from sqlalchemy.orm import Session

from security import get_password_hash
from src.Utils import TokenData
from src.Utils.UserType import UserType
from utils.service_utils import set_existing_data, check_image, generate_user_code
from utils.hide_utils import lleidahacker_show_private
from utils.service_utils import check_user

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException

from src.LleidaHacker.model import LleidaHacker as ModelLleidaHacker

from src.LleidaHacker.schema import LleidaHackerCreate as LleidaHackerCreateSchema
from src.LleidaHacker.schema import LleidaHackerUpdate as LleidaHackerUpdateSchema
from src.LleidaHacker.schema import LleidaHackerGet as LleidaHackerGetSchema
from src.LleidaHacker.schema import LleidaHackerGetAll as LleidaHackerGetAllSchema


def get_all(db: Session):
    return db.query(ModelLleidaHacker).all()


def get_lleidahacker(userId: int, db: Session, data: TokenData):
    user = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if user is None:
        raise NotFoundException("LleidaHacker not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value
                          and data.user_id == userId)):
        return parse_obj_as(LleidaHackerGetAllSchema, user)
    return parse_obj_as(LleidaHackerGetSchema, user)


def add_lleidahacker(payload: LleidaHackerCreateSchema, db: Session):
    check_user(db, payload.email, payload.nickname, payload.telephone)
    if payload.image is not None:
        payload = check_image(payload)
    new_lleidahacker = ModelLleidaHacker(**payload.dict(),
                                         code=generate_user_code(db))
    new_lleidahacker.password = get_password_hash(payload.password)
    db.add(new_lleidahacker)
    db.commit()
    db.refresh(new_lleidahacker)
    return new_lleidahacker


def update_lleidahacker(userId: int, payload: LleidaHackerUpdateSchema,
                        db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    and data.user_id == userId)):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    if payload.image is not None:
        payload = check_image(payload)
    updated = set_existing_data(lleidahacker, payload)
    lleidahacker.updated_at = date.now()
    updated.append("updated_at")
    if payload.password is not None:
        lleidahacker.password = get_password_hash(payload.password)
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker, updated


def delete_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    and data.user_id == userId)):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    db.delete(lleidahacker)
    db.commit()
    return lleidahacker


def accept_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    lleidahacker.active = 1
    lleidahacker.accepted = 1
    lleidahacker.rejected = 0
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker


def reject_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    lleidahacker.active = 0
    lleidahacker.accepted = 0
    lleidahacker.rejected = 1
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker


def activate_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    lleidahacker.active = 1
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker


def deactivate_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise NotFoundException("LleidaHacker not found")
    lleidahacker.active = 0
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker
