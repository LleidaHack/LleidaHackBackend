import glob
from fastapi import HTTPException

from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models import TokenData

from schemas.LleidaHacker import LleidaHacker as SchemaLleidaHacker

from security import check_image_exists, is_service_token

from sqlalchemy.orm import Session


async def get_all(db: Session):
    return db.query(ModelLleidaHacker).all()


async def get_lleidahacker(userId: int, db: Session):
    return db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()


async def add_lleidahacker(payload: SchemaLleidaHacker, db: Session):
    # if not checkImage(payload.image_id):
    # raise HTTPException(status_code=400, detail="Image not found")
    new_lleidahacker = ModelLleidaHacker(
        name=payload.name,
        nickname=payload.nickname,
        birthdate=payload.birthdate,
        food_restrictions=payload.food_restrictions,
        telephone=payload.telephone,
        address=payload.address,
        shirt_size=payload.shirt_size,
        nif=payload.nif,
        student=payload.student,
        role=payload.role,
        group=payload.group,
        active=payload.active,
        image_id=payload.image_id,
        github=payload.github)
    db.add(new_lleidahacker)
    db.commit()
    db.refresh(new_lleidahacker)
    return new_lleidahacker


async def update_lleidahacker(userId: int, payload: SchemaLleidaHacker,
                              db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker" or data.user_id != userId:
            raise Exception("Not authorized")
    # if check_image_exists(lleidahacker.image_id)
    lleidahacker = db.query(ModelLleidaHacker).filter(
        ModelLleidaHacker.id == userId).first()
    if lleidahacker is None:
        raise Exception("LleidaHacker not found")
    lleidahacker.name = payload.name
    lleidahacker.nickname = payload.nickname
    lleidahacker.birthdate = payload.birthdate
    lleidahacker.food_restrictions = payload.food_restrictions
    lleidahacker.telephone = payload.telephone
    lleidahacker.address = payload.address
    lleidahacker.shirt_size = payload.shirt_size
    lleidahacker.nif = payload.nif
    lleidahacker.student = payload.student
    lleidahacker.role = payload.role
    lleidahacker.group = payload.group
    lleidahacker.active = payload.active
    lleidahacker.image_id = payload.image_id
    lleidahacker.github = payload.github
    db.commit()
    db.refresh(lleidahacker)
    return lleidahacker


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
