from schemas.Company import CompanyUser as SchemaCompanyUser
from schemas.Company import CompanyUserUpdate as SchemaCompanyUserUpdate

from database import get_db
from security import create_access_token, oauth_schema, create_refresh_token

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.companyuser as companyuser_service

from security import get_data_from_token

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
)


@router.post("/signup")
async def signup(payload: SchemaCompanyUser,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_companyuser = await companyuser_service.add_company_user(payload, db)
    token = create_access_token(new_companyuser)
    refresh_token = create_refresh_token(new_companyuser)
    return {
        "success": True,
        "created_id": new_companyuser.id,
        "token": token,
        "refresh_token": refresh_token
    }


@router.get("/all")
async def get_company_users(db: Session = Depends(get_db),
                            token: str = Depends(oauth_schema)):
    return companyuser_service.get_companyusers(db)


@router.get("/{companyUserId}")
async def get_company_user(companyUserId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           token: str = Depends(oauth_schema)):
    return companyuser_service.get_companyuser(db, companyUserId)


# @router.post("/")
# async def add_company_user(payload: SchemaCompanyUser,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            token: str = Depends(oauth_schema)):
#     new_companyuser = await companyuser_service.add_company_user(db, payload)
#     return {"success": True, "created_id": new_companyuser.id}


@router.put("/{companyUserId}")
async def update_company_user(companyUserId: int,
                              payload: SchemaCompanyUserUpdate,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(oauth_schema)):
    companyuser = await companyuser_service.update_companyuser(
        db, companyUserId, payload, get_data_from_token(token))
    return {"success": True, "updated_id": companyuser.id}


@router.delete("/{companyUserId}")
async def delete_company_user(companyUserId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(oauth_schema)):
    companyuser = await companyuser_service.delete_companyuser(
        db, companyUserId, get_data_from_token(token))
    return {"success": True, "deleted_id": companyuser.id}
