from datetime import date
from sqlalchemy.orm import Session

from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models import TokenData
from models.UserType import UserType

from schemas.LleidaHacker import LleidaHacker as SchemaLleidaHacker
from schemas.LleidaHacker import LleidaHackerUpdate as SchemaLleidaHackerUpdate

from security import check_image_exists, get_password_hash

from utils.service_utils import set_existing_data, check_image

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException


async def get_all(db: Session):
    return db.query(ModelLleidaHacker).all()


async def get_lleidahacker(userId: int, db: Session):
    user = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if user is None:
        raise NotFoundException("LleidaHacker not found")
    return user


async def add_lleidahacker(payload: SchemaLleidaHacker, db: Session):
    if payload.image is not None:
        payload = check_image(payload)
    new_lleidahacker = ModelLleidaHacker(**payload.dict())
    new_lleidahacker.password = get_password_hash(payload.password)
    db.add(new_lleidahacker)
    db.commit()
    db.refresh(new_lleidahacker)
    return new_lleidahacker


async def update_lleidahacker(userId: int, payload: SchemaLleidaHackerUpdate,
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


async def delete_lleidahacker(userId: int, db: Session, data: TokenData):
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


async def accept_lleidahacker(userId: int, db: Session, data: TokenData):
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


async def reject_lleidahacker(userId: int, db: Session, data: TokenData):
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


async def activate_lleidahacker(userId: int, db: Session, data: TokenData):
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


async def deactivate_lleidahacker(userId: int, db: Session, data: TokenData):
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
