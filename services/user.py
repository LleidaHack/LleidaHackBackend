from sqlalchemy.orm import Session
from security import get_password_hash

from models.User import User as ModelUser
from models.UserType import UserType

from schemas.User import User as SchemaUser

from utils.service_utils import check_image


async def get_all(db: Session):
    return db.query(ModelUser).all()


async def get_user(db: Session, userId: int):
    return db.query(ModelUser).filter(ModelUser.id == userId).first()


async def add_user(db: Session, payload: SchemaUser):
    new_user = ModelUser(**payload.dict())
    if payload.image is not None:
        payload = check_image(payload)
    new_user.password = get_password_hash(payload.password)
    db.add(new_user)
    db.commit()
    return new_user


async def delete_user(db: Session, userId: int):
    return await db.query(ModelUser).filter(ModelUser.id == userId).delete()


async def update_user(db: Session, userId: int, payload: SchemaUser):
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    user.name = payload.name
    user.password = payload.password
    user.nickname = payload.nickname
    user.birthdate = payload.birthdate
    user.food_restrictions = payload.food_restrictions
    user.telephone = payload.telephone
    user.address = payload.address
    user.shirt_size = payload.shirt_size
    user.image_id = payload.image_id
    db.commit()
    db.refresh(user)
    return user
