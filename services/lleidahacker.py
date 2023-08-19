import glob
from fastapi import HTTPException

from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models import TokenData

from schemas.LleidaHacker import LleidaHacker as SchemaLleidaHacker

from security import check_image_exists, is_service_token

from sqlalchemy.orm import Session

from utils.service_utils import set_existing_data

async def get_all(db: Session):
    return db.query(ModelLleidaHacker).all()


async def get_lleidahacker(userId: int, db: Session):
    return db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()


async def add_lleidahacker(payload: SchemaLleidaHacker, db: Session):
    # if not checkImage(payload.image_id):
    # raise HTTPException(status_code=400, detail="Image not found")
    payload.password = get_password_hash(payload.password)
    new_lleidahacker = ModelLleidaHacker(**payload.dict())
    db.add(new_lleidahacker)
    db.commit()
    db.refresh(new_lleidahacker)
    return new_lleidahacker


async def update_lleidahacker(userId: int, payload: SchemaLleidaHacker,
                              db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == "lleida_hacker" and data.user_id == userId)):
            raise Exception("Not authorized")
    # if check_image_exists(lleidahacker.image_id)
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    updated = set_existing_data(lleidahacker, payload)
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker, updated 


async def delete_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker" or data.user_id != userId:
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    db.delete(lleidahacker)
    db.commit()
    return lleidahacker


async def set_image(userId: int, image_id: str, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker" or data.user_id != userId:
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    if not check_image_exists(image_id):
        raise Exception("Image not found")
    lleidahacker.image_id = image_id
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker

async def accept_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    lleidahacker.active = 1
    lleidahacker.accepted = 1
    lleidahacker.rejected = 0
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker

async def reject_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    lleidahacker.active = 0
    lleidahacker.accepted = 0
    lleidahacker.rejected = 1
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker

async def activate_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    lleidahacker.active = 1
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker

async def deactivate_lleidahacker(userId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    lleidahacker.active = 0
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker