from models.Hacker import HackerGroup as ModelHackerGroup
from models.Hacker import HackerGroupUser as ModelHackerGroupUser
from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import HackerGroup as SchemaHackerGroup

from sqlalchemy.orm import Session

import string
import random


async def get_all(db: Session):
    return db.query(ModelHackerGroup).all()


async def get_hacker_group(id: int, db: Session):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == id).first()


async def add_hacker_group(payload: SchemaHackerGroup, hackerId: int,
                           db: Session):
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    # generate a random 10 letter code
    code = ''
    while True:
        code = ''.join(
            random.choice(string.ascii_uppercase) for _ in range(10))
        code_exists = db.query(ModelHackerGroup).filter(
            ModelHackerGroup.code == code).first()
        if code_exists is None:
            break
    new_hacker_group = ModelHackerGroup(**payload.dict(), code=code, members=[hacker])
    db.add(new_hacker_group)
    db.commit()
    return new_hacker_group


async def update_hacker_group(id: int, payload: SchemaHackerGroup,
                              db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).first()
    hacker_group.name = payload.name
    hacker_group.description = payload.description
    hacker_group.leader = payload.leader
    db.commit()
    return hacker_group


async def delete_hacker_group(id: int, db: Session):
    hacker_group_users = db.query(ModelHackerGroupUser).filter(
        ModelHackerGroupUser.group_id == groupId).delete()
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == id).delete()
    db.commit()
    return {'removed': True}


async def add_hacker_to_group(groupId: int, hackerId: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    if hacker_group.members is None:
        hacker_group.members = []
    hacker_group.members.append(hacker)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group


async def remove_hacker_from_group(groupId: int, hackerId: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    hacker = [h for h in hacker_group.members if h.id == hackerId]
    hacker_group.members.remove(hacker[0])
    db.commit()
    db.refresh(hacker_group)
    return hacker_group


async def set_hacker_group_leader(groupId: int, hackerId: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == groupId).first()
    hacker_group.leader_id = hackerId
    db.commit()
    db.refresh(hacker_group)
    return hacker_group
