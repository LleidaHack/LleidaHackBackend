from models.LleidaHacker import LleidaHackerGroup as ModelLleidaHackerGroup
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker


from schemas.LleidaHacker import LleidaHackerGroup as SchemaLleidaHackerGroup

from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/lleidahacker/group",
    tags=["LleidaHacker Group"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.get("/all")
async def get_lleidahacker_groups(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelLleidaHackerGroup).all()

@router.get("/{groupId}")
async def get_lleidahacker_group(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()

@router.post("/")
async def add_lleidahacker_group(payload:SchemaLleidaHackerGroup, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker_group = ModelLleidaHackerGroup(name=payload.name,
                                                    description=payload.description,
    )
    db.add(new_lleidahacker_group)
    db.commit()
    return {"success": True, "created_id": new_lleidahacker_group.id}

@router.delete("/{groupId}")
async def delete_lleidahacker_group(groupId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).delete()
    return {"success": True}

@router.get("/{groupId}/members")
async def get_lleidahacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first().members

@router.post("/{groupId}/members/{lleidahackerId}")
async def add_lleidahacker_group_member(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    new_lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    new_lleidahacker_group.members.append(new_lleidahacker)
    db.commit()
    return {"success": True}

@router.delete("/{groupId}/members/{lleidahackerId}")
async def delete_lleidahacker_group_member(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    new_lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    new_lleidahacker_group.members.remove(new_lleidahacker)
    db.commit()
    return {"success": True}

@router.put("/{groupId}/leader/{lleidahackerId}")
async def set_lleidahacker_group_leader(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker_group = db.query(ModelLleidaHackerGroup).filter(ModelLleidaHackerGroup.id == groupId).first()
    lleidahacker = db.query(ModelLleidaHacker).filter(ModelLleidaHacker.id == lleidahackerId).first()
    lleidahacker_group.leader_id = lleidahacker.user_id
    db.commit()