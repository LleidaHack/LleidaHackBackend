from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.LleidaHacker.schema import LleidaHackerGet
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupCreate
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGet
from src.impl.LleidaHackerGroup.schema import LleidaHackerGroupGetAll
from src.impl.LleidaHackerGroup.service import LleidaHackerGroupService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/lleidahacker/group",
    tags=["LleidaHacker Group"],
)

lleidahackergroup_service = LleidaHackerGroupService()


@router.get("/all", response_model=List[LleidaHackerGroupGet])
def get_all(str=Depends(JWTBearer())):
    return lleidahackergroup_service.get_all()


@router.get("/{groupId}",
            response_model=Union[LleidaHackerGroupGetAll,
                                 LleidaHackerGroupGet])
def get(groupId: int, token: BaseToken = Depends(JWTBearer())):
    return lleidahackergroup_service.get_lleidahackergroup(groupId, token)


@router.post("/")
def add(payload: LleidaHackerGroupCreate,
        token: BaseToken = Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahackergroup(
        payload, token)
    return {"success": True, "id": new_lleidahacker_group.id}


@router.delete("/{groupId}")
def delete(groupId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.delete_lleidahackergroup(
        groupId, token)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.get("/{groupId}/members", response_model=List[LleidaHackerGet])
def get_members(groupId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.get_lleidahackergroup(
        groupId, token)
    return lleidahacker_group.members


@router.post("/{groupId}/members/{lleidahackerId}")
def add_member(groupId: int,
               lleidahackerId: int,
               primary: bool = False,
               token: BaseToken = Depends(JWTBearer())):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahacker_to_group(
        groupId, lleidahackerId, primary, token)
    return {"success": True, "user_id": new_lleidahacker_group.id}


@router.delete("/{groupId}/members/{lleidahackerId}")
def delete_member(groupId: int,
                  lleidahackerId: int,
                  token: BaseToken = Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_from_group(
        groupId, lleidahackerId, token)
    return {"success": True, "deleted_id": lleidahacker_group.id}


@router.post("/{groupId}/leader/{lleidahackerId}")
def add_leader(groupId: int,
               lleidahackerId: int,
               token: BaseToken = Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.add_lleidahacker_group_leader(
        groupId, lleidahackerId, token)
    return {"success": True, "updated_id": lleidahacker_group.id}

@router.delete("/{groupId}/leader/{lleidahackerId}")
def remove_leader(groupId: int,
               lleidahackerId: int,
               token: BaseToken = Depends(JWTBearer())):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_group_leader(
        groupId, lleidahackerId, token)
    return {"success": True, "updated_id": lleidahacker_group.id}

@router.get("/sorted")
def get_sorted():
    return lleidahackergroup_service.get_sorted()