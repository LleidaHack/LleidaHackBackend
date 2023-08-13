from models.Hacker import HackerGroup as ModelHackerGroup
from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import HackerGroup as SchemaHackerGroup

from sqlalchemy.orm import Session

async def get_all(db: Session):
    return db.query(ModelHackerGroup).all()

async def get_hacker_group(id: int, db: Session):
    return db.query(ModelHackerGroup).filter(ModelHackerGroup.id == id).first()

async def add_hacker_group(payload: SchemaHackerGroup, db: Session):
    new_hacker_group = ModelHackerGroup(name=payload.name,
                                        description=payload.description,
    )
    db.add(new_hacker_group)
    db.commit()
    return new_hacker_group

async def update_hacker_group(id: int, payload: SchemaHackerGroup, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == id).first()
    hacker_group.name = payload.name
    hacker_group.description = payload.description
    hacker_group.leader = payload.leader
    db.commit()
    return hacker_group

async def delete_hacker_group(id: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == id).delete()
    db.commit()
    return hacker_group

async def add_hacker_to_group(groupId: int, hackerId: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    hacker_group.members.append(hacker)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group

async def remove_hacker_from_group(groupId: int, hackerId: int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker_group.members.remove(hackerId)
    db.commit()
    db.refresh(hacker_group)
    return hacker_group

async def set_hacker_group_leader(groupId:int, hackerId:int, db: Session):
    hacker_group = db.query(ModelHackerGroup).filter(ModelHackerGroup.id == groupId).first()
    hacker_group.leader_id = hackerId