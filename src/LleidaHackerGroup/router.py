from typing import List, Union
from security import get_data_from_token
from src.LleidaHackerGroup.schema import LleidaHackerGroupCreate as LleidaHackerGroupCreateSchema
from src.LleidaHackerGroup.schema import LleidaHackerGroupGet as LleidaHackerGroupGetSchema
from src.LleidaHackerGroup.schema import LleidaHackerGroupGetAll as LleidaHackerGroupGetAllSchema

from src.LleidaHacker.schema import LleidaHackerGet as LleidaHackerGetSchema
from utils.auth_bearer import JWTBearer

from fastapi import Depends, APIRouter

from src.LleidaHackerGroup.service import LleidaHackerGroupService

router = APIRouter(
    prefix="/lleidahacker/group",
    tags=["LleidaHacker Group"],
)

lleidahackergroup_service = LleidaHackerGroupService()

@router.get("/all", response_model=List[LleidaHackerGroupGetSchema])
def get_lleidahacker_groups(str=Depends(JWTBearer())):
    return lleidahackergroup_service.get_all()


@router.get("/{groupId}", response_model=Union[LleidaHackerGroupGetSchema, LleidaHackerGroupGetAllSchema])
def get_lleidahacker_group(groupId: int,
                           str=Depends(JWTBearer())):
    return lleidahackergroup_service.get_lleidahackergroup(groupId, get_data_from_token(str))


@router.post("/")
def add_lleidahacker_group(payload: LleidaHackerGroupCreateSchema,
                           str=Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahackergroup(payload)
    return {"success": True, "user_id": new_lleidahacker_group.id}


@router.delete("/{groupId}")
def delete_lleidahacker_group(groupId: int,
                              str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.delete_lleidahackergroup(groupId)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.get("/{groupId}/members", response_model=List[LleidaHackerGetSchema])
def get_lleidahacker_group_members(groupId: int,
                                   str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.get_lleidahackergroup(
        groupId)
    return lleidahacker_group.members


@router.post("/{groupId}/members/{lleidahackerId}")
def add_lleidahacker_group_member(groupId: int,
                                  lleidahackerId: int,
                                  str=Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahacker_to_group(
        groupId, lleidahackerId)
    return {"success": True, "user_id": new_lleidahacker_group.id}


@router.delete("/{groupId}/members/{lleidahackerId}")
def delete_lleidahacker_group_member(groupId: int,
                                     lleidahackerId: int,
                                     str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_from_group(
        groupId, lleidahackerId)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.put("/{groupId}/leader/{lleidahackerId}")
def set_lleidahacker_group_leader(groupId: int,
                                  lleidahackerId: int,
                                  str=Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.set_lleidahacker_group_leader(
        groupId, lleidahackerId)
    return {"success": True, "updated_id": lleidahacker_group.id}
