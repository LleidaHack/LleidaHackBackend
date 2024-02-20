from typing import List, Union
from fastapi import Depends, APIRouter

from security import create_all_tokens
from security import create_refresh_token
from security import get_data_from_token
from utils.auth_bearer import JWTBearer

from src.CompanyUser.service import CompanyUserService

from src.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.CompanyUser.schema import CompanyUserGetAll as CompanyUserGetAllSchema
from src.CompanyUser.schema import CompanyUserCreate as CompanyUserCreateSchema
from src.CompanyUser.schema import CompanyUserUpdate as CompanyUserUpdateSchema

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
)

companyuser_service = CompanyUserService()


@router.post("/signup")
def signup(payload: CompanyUserCreateSchema):
    new_companyuser = companyuser_service.add_company_user(payload)
    access_token, refresh_token = create_all_tokens(new_companyuser, companyuser_service.db)
    return {
        "success": True,
        "user_id": new_companyuser.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[CompanyUserGetSchema])
def get_company_users(token: str = Depends(JWTBearer())):
    return companyuser_service.get_companyusers()


@router.get("/{companyUserId}",
            response_model=Union[CompanyUserGetSchema,
                                 CompanyUserGetAllSchema])
def get_company_user(companyUserId: int,
                     token: str = Depends(JWTBearer())):
    return companyuser_service.get_companyuser(companyUserId,
                                               get_data_from_token(token))


# @router.post("/")
# def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: str = Depends(JWTBearer())):
#     new_companyuser = companyuser_service.add_company_user(db, payload)
#     return {"success": True, "user_id": new_companyuser.id}


@router.put("/{companyUserId}")
def update_company_user(companyUserId: int,
                        payload: CompanyUserUpdateSchema,
                        token: str = Depends(JWTBearer())):
    companyuser = companyuser_service.update_companyuser(companyUserId, payload, get_data_from_token(token))
    return {"success": True, "updated_id": companyuser.id}


@router.delete("/{companyUserId}")
def delete_company_user(companyUserId: int,
                        token: str = Depends(JWTBearer())):
    companyuser = companyuser_service.delete_companyuser(companyUserId, get_data_from_token(token))
    return {"success": True, "deleted_id": companyuser.id}
