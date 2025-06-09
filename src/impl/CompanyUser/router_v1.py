from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.CompanyUser.schema import CompanyUserCreate
from src.impl.CompanyUser.schema import CompanyUserGet
from src.impl.CompanyUser.schema import CompanyUserGetAll
from src.impl.CompanyUser.schema import CompanyUserUpdate
from src.impl.CompanyUser.service import CompanyUserService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import AccesToken, BaseToken, RefreshToken, VerificationToken

router = APIRouter(
    prefix="/company-user",
    tags=["CompanyUser"],
)

companyuser_service = CompanyUserService()


@router.post("/signup")
def signup(payload: CompanyUserCreate):
    new_companyuser = companyuser_service.add_company_user(payload)

    access_token = AccesToken(new_companyuser).user_set()
    refresh_token = RefreshToken(new_companyuser).user_set()
    VerificationToken(new_companyuser).user_set()
    return {
        "success": True,
        "user_id": new_companyuser.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.get("/all", response_model=List[CompanyUserGet])
def get_all(token: BaseToken = Depends(JWTBearer())):
    return companyuser_service.get_all()


@router.get("/{companyUserId}",
            response_model=Union[CompanyUserGetAll, CompanyUserGet])
def get(companyUserId: int, token: BaseToken = Depends(JWTBearer())):
    return companyuser_service.get_company_user(companyUserId, token)


# @router.post("/")
# def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: BaseToken = Depends(JWTBearer())):
#     new_companyuser = companyuser_service.add_company_user(db, payload)
#     return {"success": True, "user_id": new_companyuser.id}


@router.put("/{companyUserId}")
def update(
        companyUserId: int,
        payload: CompanyUserUpdate,
        token: BaseToken = Depends(JWTBearer()),
):
    companyuser, updated = companyuser_service.update_company_user(
        payload, companyUserId, token)
    return {"success": True, "updated_id": companyuser.id, "updated": updated}


@router.delete("/{companyUserId}")
def delete(companyUserId: int, token: BaseToken = Depends(JWTBearer())):
    companyuser = companyuser_service.delete_company_user(companyUserId, token)
    return {"success": True, "deleted_id": companyuser.id}
