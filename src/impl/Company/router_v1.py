from fastapi import APIRouter

from src.impl.Company.schema import (
    CompanyCreate,
    CompanyGet,
    CompanyGetAll,
    CompanyUpdate,
)
from src.impl.Company.service import CompanyService
from src.impl.CompanyUser.schema import CompanyUserGet
from src.impl.Event.schema import EventGet
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/company',
    tags=['Company'],
)

company_service = CompanyService()


@router.get('/all', response_model=list[CompanyGet])
def get_all():
    return company_service.get_all()


@router.post('/')
def add(payload: CompanyCreate, token: BaseToken = jwt_dependency):
    new_company = company_service.add_company(payload, token)
    return {'success': True, 'id': new_company.id}


@router.get('/{company_id}', response_model=CompanyGetAll | CompanyGet)
def get(company_id: int):
    return company_service.get_company(company_id)


@router.put('/{company_id}')
def update(company_id: int, payload: CompanyUpdate, token: BaseToken = jwt_dependency):
    company, updated = company_service.update_company(company_id, payload, token)
    return {'success': True, 'updated_id': company.id, 'updated': updated}


@router.delete('/{company_id}')
def delete(company_id: int, token: BaseToken = jwt_dependency):
    company = company_service.delete_company(company_id, token)
    return {'success': True, 'deleted_id': company.id}


# TODO: check
# #################################################################
@router.get('/{company_id}/users', response_model=list[CompanyUserGet])
def get_users(company_id: int, token: BaseToken = jwt_dependency):
    return company_service.get_company_users(company_id, token)


@router.post('/{company_id}/users/{user_id}')
def add_user(company_id: int, user_id: int, token: BaseToken = jwt_dependency):
    company = company_service.add_company_user(company_id, user_id, token)
    return {'success': True, 'updated_id': company.id}


@router.delete('/{company_id}/users/{user_id}')
def delete_user(company_id: int, user_id: int, token: BaseToken = jwt_dependency):
    company = company_service.delete_company_user(company_id, user_id, token)
    return {'success': True, 'deleted_id': company.id}


#####################################################################################
@router.get('/{company_id}/events', response_model=EventGet)
def get_events(company_id: int, token: BaseToken = jwt_dependency):
    return company_service.get_company_events(company_id)


@router.get('/tier/{tier}/', response_model=list[CompanyGet])
def get_by_tier(tier: int):
    return company_service.get_by_tier(tier)
