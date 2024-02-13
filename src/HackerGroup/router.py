from typing import List
from schemas.Hacker import HackerGroup as SchemaHackerGroup

from database import get_db
from security import get_data_from_token
from utils.auth_bearer import JWTBearer
from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.hackergroup as hackergroup_service

router = APIRouter(
    prefix="/hacker/group",
    tags=["Hacker Group"],
)


@router.get("/all")
def get_hacker_groups(db: Session = Depends(get_db),
                            str=Depends(JWTBearer())):
    return hackergroup_service.get_all(db)


@router.get("/{groupId}")
def get_hacker_group(groupId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return hackergroup_service.get_hacker_group(
        groupId, db, get_data_from_token(token))


@router.post("/")
def add_hacker_group(payload: SchemaHackerGroup,
                           response: Response,
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
                              payload: SchemaHackerGroup,
                              response: Response,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.update_hacker_group(
        groupId, payload, db)
    return {"success": True, "updated_id": hacker_group.id}


@router.delete("/{groupId}")
def delete_hacker_group(groupId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.delete_hacker_group(groupId, db)
    return {"success": True, "deleted_id": hacker_group.id}


@router.get("/{groupId}/members")
def get_hacker_group_members(groupId: int,
                                   response: Response,
                                   db: Session = Depends(get_db),
                                   str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.get_hacker_group(groupId, db)
    return {"success": True, "members": hacker_group.members}


@router.post("/{groupId}/members/{hackerId}")
def add_hacker_to_group(groupId: int,
                              hackerId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group(
        groupId, hackerId, db, get_data_from_token(str))
    return {"success": True, "added_id": hacker_group.id}


@router.post("/{group_code}/members_by_code/{hacker_id}")
def add_hacker_to_group_by_code(group_code: str,
                                      hacker_id: int,
                                      response: Response,
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
