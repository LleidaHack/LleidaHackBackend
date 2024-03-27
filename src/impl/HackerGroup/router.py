from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.HackerGroup.schema import \
    HackerGroupCreate as HackerGroupCreateSchema
from src.impl.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema
from src.impl.HackerGroup.schema import \
    HackerGroupGetAll as HackerGroupGetAllSchema
from src.impl.HackerGroup.schema import \
    HackerGroupUpdate as HackerGroupUpdateSchema
from src.impl.HackerGroup.service import HackerGroupService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/hacker/group",
    tags=["Hacker Group"],
)

hackergroup_service = HackerGroupService()


@router.get("/all", response_model=List[HackerGroupGetSchema])
def get_all(str=Depends(JWTBearer())):
    return hackergroup_service.get_all()


@router.get("/{groupId}",
            response_model=Union[HackerGroupGetAllSchema,
                                 HackerGroupGetSchema])
def get(groupId: int, token: BaseToken = Depends(JWTBearer())):
    return hackergroup_service.get_hacker_group(groupId, token)


@router.post("/")
def add(payload: HackerGroupCreateSchema,
                     token: BaseToken = Depends(JWTBearer())):
    new_hacker_group = hackergroup_service.add_hacker_group(payload, token)
    #hackergroup_service.add_hacker_to_group(new_hacker_group.id, token["user_id"], db)
    #hackergroup_service.set_hacker_group_leader(new_hacker_group.id, token['user_id'], db)
    return {
        "success": True,
        "group_id": new_hacker_group.id,
        "code": new_hacker_group.code
    }


@router.put("/{groupId}")
def update(groupId: int,
                        payload: HackerGroupUpdateSchema,
                        str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.update_hacker_group(groupId, payload)
    return {"success": True, "updated_id": hacker_group.id}


@router.delete("/{groupId}")
def delete(groupId: int, str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.delete_hacker_group(groupId)
    return {"success": True, "deleted_id": hacker_group.id}


@router.get("/{groupId}/members", response_model=List[HackerGetSchema])
def get_members(groupId: int, str=Depends(JWTBearer())):
    hacker_group = hackergroup_service.get_hacker_group(groupId)
    return {"success": True, "members": hacker_group.members}


@router.post("/{groupId}/members/{hackerId}")
def add_hacker(groupId: int,
                        hackerId: int,
                        token: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group(
        groupId, hackerId, token)
    return {"success": True, "added_id": hacker_group.id}


@router.post("/{group_code}/members_by_code/{hacker_id}")
def add_hacker_by_code(group_code: str,
                                hacker_id: int,
                                token: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.add_hacker_to_group_by_code(
        group_code, hacker_id, token)
    return {"success": True, "added_id": hacker_group.id}


@router.delete("/{groupId}/members/{hackerId}")
def remove_hacker(groupId: int,
                             hackerId: int,
                             token: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.remove_hacker_from_group(
        groupId, hackerId, token)
    return {"success": True, "removed_id": hacker_group.id}


@router.put("/{groupId}/leader/{hackerId}")
def set_leader(groupId: int,
                            hackerId: int,
                            token: BaseToken = Depends(JWTBearer())):
    hacker_group = hackergroup_service.set_hacker_group_leader(
        groupId, hackerId, token)
    return {"success": True, "new_leader_id": hacker_group.leader_id}
