from schemas.Hacker import HackerGroup as SchemaHackerGroup

from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.hackergroup as hackergroup_service

router = APIRouter(
    prefix="/hacker/group",
    tags=["Hacker Group"],
)

@router.get("/all")
async def get_hacker_groups(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return hackergroup_service.get_all(db)

@router.get("/{groupId}")
async def get_hacker_group(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return hackergroup_service.get_hacker_group(groupId, db)

@router.post("/")
async def add_hacker_group(payload:SchemaHackerGroup, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_hacker_group = await hackergroup_service.add_hacker_group(payload, db)
    return {"success": True, "created_id": new_hacker_group.id}

@router.put("/{groupId}")
async def update_hacker_group(groupId: int, payload: SchemaHackerGroup, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    hacker_group = await hackergroup_service.update_hacker_group(groupId, payload, db)
    return {"success": True, "updated_id": hacker_group.id}

@router.delete("/{groupId}")
async def delete_hacker_group(groupId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    hacker_group = await hackergroup_service.delete_hacker_group(groupId, db)
    return {"success": True, "deleted_id": hacker_group.id}

@router.get("/{groupId}/members")
async def get_hacker_group_members(groupId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    hacker_group = await hackergroup_service.get_hacker_group(groupId, db)
    return {"success": True, "members": hacker_group.members}

@router.post("/{groupId}/members/{hackerId}")
async def add_hacker_to_group(groupId: int, hackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    hacker_group = await hackergroup_service.add_hacker_to_group(groupId, hackerId, db)
    return {"success": True, "added_id": hacker_group.id}

@router.delete("/{groupId}/members/{hackerId}")
async def remove_hacker_from_group(groupId: int, hackerId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    hacker_group = await hackergroup_service.remove_hacker_from_group(groupId, hackerId, db)
    return {"success": True, "removed_id": hacker_group.id}