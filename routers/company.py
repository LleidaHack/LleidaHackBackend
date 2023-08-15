from schemas.Company import Company as SchemaCompany
from schemas.Company import CompanyUser as SchemaCompanyUser

from database import get_db
from security import oauth_schema, get_data_from_token

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.company as company_service

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.get("/all")
async def get_companies(db: Session = Depends(get_db),
                        token: str = Depends(oauth_schema)):
    return await company_service.get_all(db)


@router.get("/{companyId}")
async def get_company(companyId: int,
                      response: Response,
                      db: Session = Depends(get_db),
                      str=Depends(oauth_schema)):
    return await company_service.get_company(db, companyId)


@router.post("/")
async def add_company(payload: SchemaCompany,
                      response: Response,
                      db: Session = Depends(get_db),
                      token: str = Depends(oauth_schema)):
    new_company = await company_service.add_company(db, payload,
                                                    get_data_from_token(token))
    return {"success": True, "created_id": new_company.id}


@router.put("/{companyId}")
async def update_company(companyId: int,
                         payload: SchemaCompany,
                         response: Response,
                         db: Session = Depends(get_db),
                         token: str = Depends(oauth_schema)):
    company = await company_service.update_company(db, companyId, payload,
                                                   get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}")
async def delete_company(companyId: int,
                         response: Response,
                         db: Session = Depends(get_db),
                         token: str = Depends(oauth_schema)):
    company = await company_service.delete_company(db, companyId,
                                                   get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}


@router.get("/{companyId}/users")
async def get_company_users(companyId: int,
                            response: Response,
                            db: Session = Depends(get_db),
                            str=Depends(oauth_schema)):
    return await company_service.get_company_users(db, companyId,
                                                   get_data_from_token(str))


@router.post("/{companyId}/users/{userId}")
async def add_company_user(companyId: int,
                           userId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           token: str = Depends(oauth_schema)):
    company = await company_service.add_company_user(
        db, companyId, userId, get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}/users/{userId}")
async def delete_company_user(companyId: int,
                              userId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(oauth_schema)):
    company = await company_service.delete_company_user(
        db, companyId, userId, get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}


@router.get("/{companyId}/events")
async def get_company_events(companyId: int,
                             response: Response,
                             db: Session = Depends(get_db),
                             str=Depends(oauth_schema)):
    return await company_service.get_company_events(db, companyId)
