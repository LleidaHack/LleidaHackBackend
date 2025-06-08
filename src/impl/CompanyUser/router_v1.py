from fastapi import APIRouter

from src.impl.CompanyUser.schema import (
    CompanyUserCreate,
    CompanyUserGet,
    CompanyUserGetAll,
    CompanyUserUpdate,
)
from src.impl.CompanyUser.service import CompanyUserService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import AccesToken, BaseToken, RefreshToken, VerificationToken

router = APIRouter(
    prefix='/company-user',
    tags=['CompanyUser'],
)

companyuser_service = CompanyUserService()


@router.post('/signup')
def signup(payload: CompanyUserCreate):
    new_companyuser = companyuser_service.add_company_user(payload)

    access_token = AccesToken(new_companyuser).user_set()
    refresh_token = RefreshToken(new_companyuser).user_set()
    VerificationToken(new_companyuser).user_set()
    return {
        'success': True,
        'user_id': new_companyuser.id,
        'access_token': access_token,
        'refresh_token': refresh_token,
    }


@router.get('/all', response_model=list[CompanyUserGet])
def get_all(token: BaseToken = jwt_dependency):
    return companyuser_service.get_all()


@router.get('/{company_user_id}', response_model=CompanyUserGetAll | CompanyUserGet)
def get(company_user_id: int, token: BaseToken = jwt_dependency):
    return companyuser_service.get_company_user(company_user_id, token)


# @router.post("/")
# def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: BaseToken = jwt_dependency):
#     new_companyuser = companyuser_service.add_company_user(db, payload)
#     return {"success": True, "user_id": new_companyuser.id}


@router.put('/{company_user_id}')
def update(
    company_user_id: int,
    payload: CompanyUserUpdate,
    token: BaseToken = jwt_dependency,
):
    companyuser, updated = companyuser_service.update_company_user(
        payload, company_user_id, token
    )
    return {'success': True, 'updated_id': companyuser.id, 'updated': updated}


@router.delete('/{company_user_id}')
def delete(company_user_id: int, token: BaseToken = jwt_dependency):
    companyuser = companyuser_service.delete_company_user(company_user_id, token)
    return {'success': True, 'deleted_id': companyuser.id}
