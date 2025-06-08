from fastapi import APIRouter

from src.impl.HackerGroup.schema import (
    HackerGroupCreate,
    HackerGroupGet,
    HackerGroupGetAll,
    HackerGroupUpdate,
)
from src.impl.HackerGroup.service import HackerGroupService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/hacker/group',
    tags=['Hacker Group'],
)

hackergroup_service = HackerGroupService()


@router.get('/all', response_model=list[HackerGroupGet])
def get_all(data: BaseToken = jwt_dependency):
    return hackergroup_service.get_all()


@router.get('/{group_id}', response_model=HackerGroupGetAll | HackerGroupGet)
def get(group_id: int, data: BaseToken = jwt_dependency):
    return hackergroup_service.get_hacker_group(group_id, data)


@router.post('/')
def add(payload: HackerGroupCreate, data: BaseToken = jwt_dependency):
    new_hacker_group = hackergroup_service.add_hacker_group(payload, data)
    # hackergroup_service.add_hacker_to_group(new_hacker_group.id, data["user_id"], db)
    # hackergroup_service.set_hacker_group_leader(new_hacker_group.id, data['user_id'], db)
    return {
        'success': True,
        'group_id': new_hacker_group.id,
        'code': new_hacker_group.code,
    }


@router.put('/{group_id}')
def update(group_id: int, payload: HackerGroupUpdate, data: BaseToken = jwt_dependency):
    hackergroup_service.update_hacker_group(group_id, payload, data)
    return {'success': True, 'updated_id': group_id}


@router.delete('/{group_id}')
def delete(group_id: int, data: BaseToken = jwt_dependency):
    hackergroup_service.delete_hacker_group(group_id, data)
    return {'success': True, 'deleted_id': group_id}


@router.get('/{group_id}/members')
def get_members(group_id: int, data: BaseToken = jwt_dependency):
    hacker_group = hackergroup_service.get_hacker_group(group_id, data)
    return {'success': True, 'members': hacker_group.members}


@router.post('/{group_id}/members/{hacker_id}')
def add_hacker(group_id: int, hacker_id: int, data: BaseToken = jwt_dependency):
    hacker_group = hackergroup_service.add_hacker_to_group(group_id, hacker_id, data)
    return {
        'success': True,
        'added_hacker_id': hacker_id,
        'added_group_id': hacker_group.id,
    }


@router.post('/{group_code}/members_by_code/{hacker_id}')
def add_hacker_by_code(
    group_code: str, hacker_id: int, data: BaseToken = jwt_dependency
):
    hacker_group = hackergroup_service.add_hacker_to_group_by_code(
        group_code, hacker_id, data
    )
    return {
        'success': True,
        'added_hacker_id': hacker_id,
        'added_group_id': hacker_group.id,
    }


@router.delete('/{group_id}/members/{hacker_id}')
def remove_hacker(group_id: int, hacker_id: int, data: BaseToken = jwt_dependency):
    hackergroup_service.remove_hacker_from_group(group_id, hacker_id, data)
    return {
        'success': True,
        'removed_hacker_id': hacker_id,
        'removed_group_id': group_id,
    }


@router.put('/{group_id}/leader/{hacker_id}')
def set_leader(group_id: int, hacker_id: int, data: BaseToken = jwt_dependency):
    hacker_group = hackergroup_service.set_hacker_group_leader(
        group_id, hacker_id, data
    )
    return {'success': True, 'new_leader_id': hacker_group.leader_id}
