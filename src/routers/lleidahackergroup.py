from schemas.LleidaHacker import LleidaHackerGroup as SchemaLleidaHackerGroup

from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.lleidahackergroup as lleidahackergroup_service

router = APIRouter(
    prefix="/lleidahacker/group",
    tags=["LleidaHacker Group"],
)

@router.get("/all")
async def get_lleidahacker_groups(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return lleidahackergroup_service.get_all(db)

@router.get("/{groupId}")
async def get_lleidahacker_group(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return lleidahackergroup_service.get_lleidahackergroup(groupId, db)

@router.post("/")
async def add_lleidahacker_group(payload:SchemaLleidaHackerGroup, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker_group = await lleidahackergroup_service.add_lleidahackergroup(payload, db)
    return {"success": True, "created_id": new_lleidahacker_group.id}

@router.delete("/{groupId}")
async def delete_lleidahacker_group(groupId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker_group = await lleidahackergroup_service.delete_lleidahackergroup(groupId, db)
    return {"success": True, "deleted_id": lleidahacker_group.id}

@router.get("/{groupId}/members")
async def get_lleidahacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker_group = await lleidahackergroup_service.get_lleidahackergroup(groupId, db)
    return lleidahacker_group.members

@router.post("/{groupId}/members/{lleidahackerId}")
async def add_lleidahacker_group_member(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker_group = await lleidahackergroup_service.add_lleidahacker_to_group(groupId, lleidahackerId, db)
    return {"success": True, "created_id": new_lleidahacker_group.id}

@router.delete("/{groupId}/members/{lleidahackerId}")
async def delete_lleidahacker_group_member(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker_group = await lleidahackergroup_service.remove_lleidahacker_from_group(groupId, lleidahackerId, db)
    return {"success": True, "deleted_id": lleidahacker_group.id}

@router.put("/{groupId}/leader/{lleidahackerId}")
async def set_lleidahacker_group_leader(groupId: int, lleidahackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker_group = await lleidahackergroup_service.set_lleidahacker_group_leader(groupId, lleidahackerId, db)
    return {"success": True, "updated_id": lleidahacker_group.id}