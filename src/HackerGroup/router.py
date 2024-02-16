from typing import List, Union
from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session

from database import get_db
from security import get_data_from_token
from utils.auth_bearer import JWTBearer

import src.HackerGroup.service as hackergroup_service

from src.Hacker.schema import HackerGet as HackerGetSchema
from src.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema
from src.HackerGroup.schema import HackerGroupGetAll as HackerGroupGetAllSchema
from src.HackerGroup.schema import HackerGroupCreate as HackerGroupCreateSchema
from src.HackerGroup.schema import HackerGroupUpdate as HackerGroupUpdateSchema

router = APIRouter(
    prefix="/hacker/group",
    tags=["Hacker Group"],
)


@router.get("/all", response_model=List[HackerGroupGetSchema])
def get_hacker_groups(db: Session = Depends(get_db),
                            str=Depends(JWTBearer())):
    return hackergroup_service.get_all(db)


@router.get("/{groupId}", response_model=Union[HackerGroupGetSchema, HackerGroupGetAllSchema])
def get_hacker_group(groupId: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return hackergroup_service.get_hacker_group(
        groupId, db, get_data_from_token(token))


@router.post("/")
def add_hacker_group(payload: HackerGroupCreateSchema,
                           db: Session = Depends(get_db),
                           str=Depends(JWTBearer())):
    new_hacker_group = hackergroup_service.add_hacker_group(
        payload, db, get_data_from_token(str))
    #hackergroup_service.add_hacker_to_group(new_hacker_group.id, token["user_id"], db)
    #hackergroup_service.set_hacker_group_leader(new_hacker_group.id, token['user_id'], db)
    return {
        "success": True,
        "group_id": new_hacker_group.id,
        "code": new_hacker_group.code
    }


@router.put("/{groupId}")
def update_hacker_group(groupId: int,
                              payload: HackerGroupUpdateSchema,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.update_hacker_group(
        groupId, payload, db)
    return {"success": True, "updated_id": hacker_group.id}


@router.delete("/{groupId}")
def delete_hacker_group(groupId: int,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.delete_hacker_group(groupId, db)
    return {"success": True, "deleted_id": hacker_group.id}


@router.get("/{groupId}/members", response_model=List[HackerGetSchema])
def get_hacker_group_members(groupId: int,
                                   db: Session = Depends(get_db),
                                   str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.get_hacker_group(groupId, db)
    return {"success": True, "members": hacker_group.members}


@router.post("/{groupId}/members/{hackerId}")
def add_hacker_to_group(groupId: int,
                              hackerId: int,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group(
        groupId, hackerId, db, get_data_from_token(str))
    return {"success": True, "added_id": hacker_group.id}


@router.post("/{group_code}/members_by_code/{hacker_id}")
def add_hacker_to_group_by_code(group_code: str,
                                      hacker_id: int,
                                      db: Session = Depends(get_db),
                                      str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group_by_code(
        group_code, hacker_id, db, get_data_from_token(str))
    return {"success": True, "added_id": hacker_group.id}


@router.delete("/{groupId}/members/{hackerId}")
def remove_hacker_from_group(groupId: int,
                                   hackerId: int,
                                   db: Session = Depends(get_db),
                                   str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.remove_hacker_from_group(
        groupId, hackerId, db, get_data_from_token(str))
    return {"success": True, "removed_id": hacker_group.id}


@router.put("/{groupId}/leader/{hackerId}")
def set_hacker_group_leader(groupId: int,
                                  hackerId: int,
                                  db: Session = Depends(get_db),
                                  str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.set_hacker_group_leader(
        groupId, hackerId, db, get_data_from_token(str))
    return {"success": True, "new_leader_id": hacker_group.leader_id}
