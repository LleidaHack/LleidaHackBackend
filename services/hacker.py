from models.Hacker import Hacker as ModelHacker
from models.TokenData import TokenData

from schemas.Hacker import Hacker as SchemaHacker

from sqlalchemy.orm import Session

from security import get_password_hash


async def get_all(db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == "lleida_hacker" or data.type == "hacker")):
            raise Exception("Not authorized")
    return db.query(ModelHacker).all()


async def get_hacker(hackerId: int, db: Session):
    return db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()


async def add_hacker(payload: SchemaHacker, db: Session):
    payload.password = get_password_hash(payload.password)
    new_hacker = ModelHacker(**payload.dict())
    db.add(new_hacker)
    db.commit()
    db.refresh(new_hacker)
    return new_hacker


async def remove_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == "lleida_hacker" or
                                      (data.type == "hacker"
                                       and data.user_id == hackerId))):
            raise Exception("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if not hacker:
        raise Exception("Hacker not found")
    db.delete(hacker)
    db.commit()
    return hacker


async def update_hacker(hackerId: int, payload: SchemaHacker, db: Session,
                        data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == "lleida_hacker" or (data.type == "hacker" and data.user_id == hackerId))):
            raise Exception("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise Exception("Hacker not found")
    hacker.name = payload.name
    hacker.nickname = payload.nickname
    hacker.birthdate = payload.birthdate
    hacker.food_restrictions = payload.food_restrictions
    hacker.telephone = payload.telephone
    hacker.address = payload.address
    hacker.shirt_size = payload.shirt_size
    hacker.image_id = payload.image_id,
    db.commit()
    db.refresh(hacker)
    return hacker


async def ban_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise Exception("Hacker not found")
    hacker.banned = 1
    db.commit()
    db.refresh(hacker)
    return hacker


async def unban_hacker(hackerId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == "lleida_hacker"):
            raise Exception("Not authorized")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker is None:
        raise Exception("Hacker not found")
    hacker.banned = 0
    db.commit()
    db.refresh(hacker)
    return hacker
