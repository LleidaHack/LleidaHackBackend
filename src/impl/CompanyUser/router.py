from typing import List, Union
from fastapi import Depends, APIRouter

from src.utils.Token import AccesToken, BaseToken, RefreshToken, VerificationToken
from src.utils.JWTBearer import JWTBearer

from src.impl.CompanyUser.service import CompanyUserService

from src.impl.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.impl.CompanyUser.schema import CompanyUserGetAll as CompanyUserGetAllSchema
from src.impl.CompanyUser.schema import CompanyUserCreate as CompanyUserCreateSchema
from src.impl.CompanyUser.schema import CompanyUserUpdate as CompanyUserUpdateSchema

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
)

companyuser_service = CompanyUserService()


@router.post("/signup")
def signup(payload: CompanyUserCreateSchema):
    new_companyuser = companyuser_service.add_company_user(payload)

    access_token = AccesToken(new_companyuser).save_to_user()
    refresh_token = RefreshToken(new_companyuser).save_to_user()
    VerificationToken(new_companyuser).save_to_user()
    return {
        "success": True,
        "user_id": new_companyuser.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[CompanyUserGetSchema])
def get_company_users(token: BaseToken = Depends(JWTBearer())):
    return companyuser_service.get_all()


@router.get("/{companyUserId}",
            response_model=Union[CompanyUserGetAllSchema, CompanyUserGetSchema])
def get_company_user(companyUserId: int,
                     token: BaseToken = Depends(JWTBearer())):
    return companyuser_service.get_company_user(companyUserId, token)


# @router.post("/")
# def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: BaseToken = Depends(JWTBearer())):
#     new_companyuser = companyuser_service.add_company_user(db, payload)
#     return {"success": True, "user_id": new_companyuser.id}


@router.put("/{companyUserId}")
def update_company_user(companyUserId: int,
                        payload: CompanyUserUpdateSchema,
                        token: BaseToken = Depends(JWTBearer())):
    companyuser = companyuser_service.update_companyuser(
        companyUserId, payload, token)
    return {"success": True, "updated_id": companyuser.id}


@router.delete("/{companyUserId}")
def delete_company_user(companyUserId: int,
                        token: BaseToken = Depends(JWTBearer())):
    companyuser = companyuser_service.delete_companyuser(companyUserId, token)
    return {"success": True, "deleted_id": companyuser.id}
