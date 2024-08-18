from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Hacker.schema import HackerGet
from src.impl.HackerGroup.schema import HackerGroupCreate
from src.impl.HackerGroup.schema import HackerGroupGet
from src.impl.HackerGroup.schema import HackerGroupGetAll
from src.impl.HackerGroup.schema import HackerGroupUpdate
from src.impl.HackerGroup.service import HackerGroupService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/hacker/group",
    tags=["Hacker Group"],
)

hackergroup_service = HackerGroupService()


@router.get("/all", response_model=List[HackerGroupGet])
def get_all(data: BaseToken = Depends(JWTBearer())):
    return hackergroup_service.get_all()


@router.get("/{groupId}",
            response_model=Union[HackerGroupGetAll,
                                 HackerGroupGet])
def get(groupId: int, data: BaseToken = Depends(JWTBearer())):
    return hackergroup_service.get_hacker_group(groupId, data)


@router.post("/")
def add(payload: HackerGroupCreate,
        data: BaseToken = Depends(JWTBearer())):
    new_hacker_group = hackergroup_service.add_hacker_group(payload, data)
    #hackergroup_service.add_hacker_to_group(new_hacker_group.id, data["user_id"], db)
    #hackergroup_service.set_hacker_group_leader(new_hacker_group.id, data['user_id'], db)
    return {
        "success": True,
        "group_id": new_hacker_group.id,
        "code": new_hacker_group.code
    }


@router.put("/{groupId}")
def update(groupId: int,
           payload: HackerGroupUpdate,
           data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.update_hacker_group(
        groupId, payload, data)
    return {"success": True, "updated_id": hacker_group.id}


@router.delete("/{groupId}")
def delete(groupId: int, data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.delete_hacker_group(groupId, data)
    return {"success": True, "deleted_id": hacker_group.id}


@router.get("/{groupId}/members", response_model=List[HackerGet])
def get_members(groupId: int, data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.get_hacker_group(groupId, data)
    return {"success": True, "members": hacker_group.members}


@router.post("/{groupId}/members/{hackerId}")
def add_hacker(groupId: int,
               hackerId: int,
               data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group(
        groupId, hackerId, data)
    return {"success": True, "added_id": hacker_group.id}


@router.post("/{group_code}/members_by_code/{hacker_id}")
def add_hacker_by_code(group_code: str,
                       hacker_id: int,
                       data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group_by_code(
        group_code, hacker_id, data)
    return {"success": True, "added_id": hacker_group.id}


@router.delete("/{groupId}/members/{hackerId}")
def remove_hacker(groupId: int,
                  hackerId: int,
                  data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.remove_hacker_from_group(
        groupId, hackerId, data)
    return {"success": True, "removed_id": hacker_group.id}


@router.put("/{groupId}/leader/{hackerId}")
def set_leader(groupId: int,
               hackerId: int,
               data: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.set_hacker_group_leader(
        groupId, hackerId, data)
    return {"success": True, "new_leader_id": hacker_group.leader_id}
