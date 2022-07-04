from sqlalchemy.orm import Session
from security import get_password_hash

from models.User import User as ModelUser

from schemas.User import User as SchemaUser



def get_all(db: Session):
    return db.query(ModelUser).all()

async def get_user(db: Session, userId: int):
    return await db.query(ModelUser).filter(ModelUser.id == userId).first()

async def add_user(db: Session, payload: SchemaUser):
    new_user = ModelUser(name=payload.name, 
                         email=payload.email,
                         password=get_password_hash(payload.password),
                         nickname=payload.nickname,
                         birthdate = payload.birthdate,
                         food_restrictions=payload.food_restrictions,
                         telephone=payload.telephone,
                         address=payload.address,
                         shirt_size=payload.shirt_size)
    db.add(new_user)
    db.commit()
    return new_user

async def delete_user(db: Session, userId: int):
    return await db.query(ModelUser).filter(ModelUser.id == userId).delete()

async def update_user(db: Session, userId: int, payload: SchemaUser):
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    user.name = payload.name
    user.email = payload.email
    user.password = payload.password
    user.nickname = payload.nickname
    user.birthdate = payload.birthdate
    user.food_restrictions = payload.food_restrictions
    user.telephone = payload.telephone
    user.address = payload.address
    user.shirt_size = payload.shirt_size
    db.commit()
    db.refresh(user)
    return user

