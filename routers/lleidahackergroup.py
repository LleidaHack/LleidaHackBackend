from src.LleidaHacker.schema import LleidaHackerGroup as SchemaLleidaHackerGroup

from database import get_db
from utils.auth_bearer import JWTBearer

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.lleidahackergroup as lleidahackergroup_service

router = APIRouter(
    prefix="/lleidahacker/group",
    tags=["LleidaHacker Group"],
)


@router.get("/all")
def get_lleidahacker_groups(db: Session = Depends(get_db),
                                  str=Depends(JWTBearer())):
    return lleidahackergroup_service.get_all(db)


@router.get("/{groupId}")
def get_lleidahacker_group(groupId: int,
                                 response: Response,
                                 db: Session = Depends(get_db),
                                 str=Depends(JWTBearer())):
    return lleidahackergroup_service.get_lleidahackergroup(groupId, db)


@router.post("/")
def add_lleidahacker_group(payload: SchemaLleidaHackerGroup,
                                 response: Response,
                                 db: Session = Depends(get_db),
                                 str=Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahackergroup(
        payload, db)
    return {"success": True, "user_id": new_lleidahacker_group.id}


@router.delete("/{groupId}")
def delete_lleidahacker_group(groupId: int,
                                    response: Response,
                                    db: Session = Depends(get_db),
                                    str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.delete_lleidahackergroup(
        groupId, db)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.get("/{groupId}/members")
def get_lleidahacker_group_members(groupId: int,
                                         response: Response,
                                         db: Session = Depends(get_db),
                                         str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.get_lleidahackergroup(
        groupId, db)
    return lleidahacker_group.members


@router.post("/{groupId}/members/{lleidahackerId}")
def add_lleidahacker_group_member(groupId: int,
                                        lleidahackerId: int,
                                        response: Response,
                                        db: Session = Depends(get_db),
                                        str=Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahacker_to_group(
        groupId, lleidahackerId, db)
    return {"success": True, "user_id": new_lleidahacker_group.id}


@router.delete("/{groupId}/members/{lleidahackerId}")
def delete_lleidahacker_group_member(groupId: int,
                                           lleidahackerId: int,
                                           response: Response,
                                           db: Session = Depends(get_db),
                                           str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_from_group(
        groupId, lleidahackerId, db)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.put("/{groupId}/leader/{lleidahackerId}")
def set_lleidahacker_group_leader(groupId: int,
                                        lleidahackerId: int,
                                        response: Response,
                                        db: Session = Depends(get_db),
                                        str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.set_lleidahacker_group_leader(
        groupId, lleidahackerId, db)
    return {"success": True, "updated_id": lleidahacker_group.id}
