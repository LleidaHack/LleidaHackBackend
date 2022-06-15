from schemas.Company import CompanyUser as SchemaCompanyUser

from database import get_db
from security import create_access_token, oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.companyuser as companyuser_service

router = APIRouter(
    prefix="/company/user",
    tags=["Company User"],
)

@router.post("/signup")
async def signup(payload: SchemaCompanyUser, response: Response, db: Session = Depends(get_db)):
    new_companyuser = companyuser_service.add_companyuser(db, payload)
    token = create_access_token(new_companyuser)
    return {"success": True, "token": token}

@router.get("/all")
async def get_company_users(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return companyuser_service.get_companyusers(db)

@router.get("/{companyUserId}")
async def get_company_user(companyUserId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return companyuser_service.get_companyuser(db, companyUserId)

@router.post("/")
async def add_company_user(payload:SchemaCompanyUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_companyuser = companyuser_service.add_companyuser(db, payload)
    return {"success": True, "created_id": new_companyuser.id}


@router.put("/{companyUserId}")
async def update_company_user(companyUserId: int, payload: SchemaCompanyUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    companyuser = companyuser_service.update_companyuser(db, companyUserId, payload)
    return {"success": True, "updated_id": companyuser.id}

@router.delete("/{companyUserId}")
async def delete_company_user(companyUserId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    companyuser = companyuser_service.delete_companyuser(db, companyUserId)
    return {"success": True, "deleted_id": companyuser.id}
