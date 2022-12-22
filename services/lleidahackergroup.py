from models.LleidaHacker import LleidaHackerGroup as ModelLleidaHackerGroup
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker


from schemas.LleidaHacker import LleidaHackerGroup as SchemaLleidaHackerGroup


from sqlalchemy.orm import Session

async def get_all(db: Session):
    return db.query(ModelLleidaHackerGroup).all()

async def get_lleidahackergroup(groupId: int, db: Session):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()

async def add_lleidahackergroup(payload: SchemaLleidaHackerGroup, db: Session):
    new_lleidahacker_group = ModelLleidaHackerGroup(name=payload.name,
                                                    description=payload.description,
    )
    db.add(new_lleidahacker_group)
    db.commit()
    db.refresh(new_lleidahacker_group)
    return new_lleidahacker_group

async def update_lleidahackergroup(groupId: int, payload: SchemaLleidaHackerGroup, db: Session):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    lleidahacker_group.name = payload.name
    lleidahacker_group.description = payload.description
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group

async def delete_lleidahackergroup(groupId: int, db: Session):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    db.delete(lleidahacker_group)
    db.commit()
    return lleidahacker_group

async def add_lleidahacker_to_group(groupId: int, lleidahackerId: int, db: Session):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    lleidahacker_group.members.append(lleidahacker)
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group

async def remove_lleidahacker_from_group(groupId: int, lleidahackerId: int, db: Session):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    lleidahacker_group.members.remove(lleidahacker)
    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group

async def set_lleidahacker_group_leader(groupId: int, lleidahackerId: int, db: Session):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    lleidahacker_group.leader_id = lleidahacker.id
    lleidahacker_group.leader = lleidahacker

    db.commit()
    db.refresh(lleidahacker_group)
    return lleidahacker_group