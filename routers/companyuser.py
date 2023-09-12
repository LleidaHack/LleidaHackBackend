from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Company import CompanyUser as SchemaCompanyUser
from schemas.Company import CompanyUserUpdate as SchemaCompanyUserUpdate

import services.companyuser as companyuser_service

from database import get_db

from security import create_token_pair
from security import create_refresh_token
from security import get_data_from_token

from utils.auth_bearer import JWTBearer

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
)


@router.post("/signup")
async def signup(payload: SchemaCompanyUser,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_companyuser = await companyuser_service.add_company_user(payload, db)
    access_token, refresh_token = await create_token_pair(new_companyuser, db)
    return {
        "success": True,
        "user_id": new_companyuser.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all")
async def get_company_users(db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    return companyuser_service.get_companyusers(db)


@router.get("/{companyUserId}")
async def get_company_user(companyUserId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return companyuser_service.get_companyuser(db, companyUserId, get_data_from_token(token))


# @router.post("/")
# async def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: str = Depends(JWTBearer())):
#     new_companyuser = await companyuser_service.add_company_user(db, payload)
#     return {"success": True, "user_id": new_companyuser.id}


@router.put("/{companyUserId}")
async def update_company_user(companyUserId: int,
                              payload: SchemaCompanyUserUpdate,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    companyuser = await companyuser_service.update_companyuser(
        db, companyUserId, payload, get_data_from_token(token))
    return {"success": True, "updated_id": companyuser.id}


@router.delete("/{companyUserId}")
async def delete_company_user(companyUserId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    companyuser = await companyuser_service.delete_companyuser(
        db, companyUserId, get_data_from_token(token))
    return {"success": True, "deleted_id": companyuser.id}
