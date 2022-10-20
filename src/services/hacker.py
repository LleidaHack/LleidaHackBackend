from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import Hacker as SchemaHacker


from sqlalchemy.orm import Session

from security import get_password_hash

async def get_all(db: Session):
    return db.query(ModelHacker).all()

async def get_hacker(hackerId: int, db: Session):
    return db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()

async def add_hacker(payload:SchemaHacker, db: Session):
    new_hacker = ModelHacker(name=payload.name,
                             email=payload.email,
                             linkedin=payload.linkedin,
                             github=payload.github,
                             password=get_password_hash(payload.password),
                             nickname=payload.nickname,
                             birthdate = payload.birthdate,
                             food_restrictions=payload.food_restrictions,
                             telephone=payload.telephone,
                             address=payload.address,
                             shirt_size=payload.shirt_size,
                             image_id=payload.image_id,
                             )
    db.add(new_hacker)
    db.commit()
    db.refresh(new_hacker)
    return new_hacker

async def remove_hacker(hackerId: int, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    db.delete(hacker)
    db.commit()
    return hacker

async def update_hacker(hackerId: int, payload:SchemaHacker, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker.name = payload.name
    hacker.email = payload.email
    hacker.password = payload.password
    hacker.nickname = payload.nickname
    hacker.birthdate = payload.birthdate
    hacker.food_restrictions = payload.food_restrictions
    hacker.telephone = payload.telephone
    hacker.address = payload.address
    hacker.shirt_size = payload.shirt_size
    hacker.image_id=payload.image_id,

    db.commit()
    return hacker

async def ban_hacker(hackerId: int, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker.banned = True
    db.commit()
    db.refresh(hacker)
    return hacker

async def unban_hacker(hackerId: int, db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker.banned = False
    db.commit()
    db.refresh(hacker)
    return hacker

