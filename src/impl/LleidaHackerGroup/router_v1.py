from fastapi import APIRouter

from src.impl.LleidaHacker.schema import LleidaHackerGet
from src.impl.LleidaHackerGroup.schema import (
    LleidaHackerGroupCreate,
    LleidaHackerGroupGet,
    LleidaHackerGroupGetAll,
)
from src.impl.LleidaHackerGroup.service import LleidaHackerGroupService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/lleidahacker/group',
    tags=['LleidaHacker Group'],
)

lleidahackergroup_service = LleidaHackerGroupService()


@router.get('/all', response_model=list[LleidaHackerGroupGet])
def get_all(token: BaseToken = jwt_dependency):
    return lleidahackergroup_service.get_all()


@router.get(
    '/{group_id}', response_model=LleidaHackerGroupGetAll | LleidaHackerGroupGet
)
def get(group_id: int, token: BaseToken = jwt_dependency):
    return lleidahackergroup_service.get_lleidahackergroup(group_id, token)


@router.post('/')
def add(payload: LleidaHackerGroupCreate, token: BaseToken = jwt_dependency):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahackergroup(
        payload, token
    )
    return {'success': True, 'id': new_lleidahacker_group.id}


@router.delete('/{group_id}')
def delete(group_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_group = lleidahackergroup_service.delete_lleidahackergroup(
        group_id, token
    )
    return {'success': True, 'deleted_id': lleidahacker_group.id}


@router.get('/{group_id}/members', response_model=list[LleidaHackerGet])
def get_members(group_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_group = lleidahackergroup_service.get_lleidahackergroup(
        group_id, token
    )
    return lleidahacker_group.members


@router.post('/{group_id}/members/{lleidahacker_id}')
def add_member(
    group_id: int,
    lleidahacker_id: int,
    primary: bool = False,
    token: BaseToken = jwt_dependency,
):
    new_lleidahacker_group = lleidahackergroup_service.add_lleidahacker_to_group(
        group_id, lleidahacker_id, primary, token
    )
    return {'success': True, 'user_id': new_lleidahacker_group.id}


@router.delete('/{group_id}/members/{lleidahacker_id}')
def delete_member(
    group_id: int, lleidahacker_id: int, token: BaseToken = jwt_dependency
):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_from_group(
        group_id, lleidahacker_id, token
    )
    return {'success': True, 'deleted_id': lleidahacker_group.id}


@router.post('/{group_id}/leader/{lleidahacker_id}')
def add_leader(group_id: int, lleidahacker_id: int, token: BaseToken = jwt_dependency):
    lleidahacker_group = lleidahackergroup_service.add_lleidahacker_group_leader(
        group_id, lleidahacker_id, token
    )
    return {'success': True, 'updated_id': lleidahacker_group.id}


@router.delete('/{group_id}/leader/{lleidahacker_id}')
def remove_leader(
    group_id: int, lleidahacker_id: int, token: BaseToken = jwt_dependency
):
    lleidahacker_group = lleidahackergroup_service.remove_lleidahacker_group_leader(
        group_id, lleidahacker_id, token
    )
    return {'success': True, 'updated_id': lleidahacker_group.id}


@router.put('/sorted/')
def get_sorted():
    return lleidahackergroup_service.get_sorted()
