from typing import List, Union
from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session
# from src.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema

from database import get_db
from security import get_data_from_token
from utils.auth_bearer import JWTBearer

from src.Company import service as company_service

from src.Company.schema import CompanyGet as CompanyGetSchema
from src.Company.schema import CompanyGetAll as CompanyGetAllSchema
from src.Company.schema import CompanyCreate as CompanyCreateSchema
from src.Company.schema import CompanyUpdate as CompanyUpdateSchema
from src.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.Event.schema import EventGet as EventGetSchema


router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.get("/all", response_model=List[CompanyGetSchema])
def get_companies(db: Session = Depends(get_db)):
    return company_service.get_all(db)


@router.get("/{companyId}", response_model=Union[CompanyGetSchema, CompanyGetAllSchema])
def get_company(companyId: int,
                db: Session = Depends(get_db)):
    return company_service.get_company(db, companyId)


@router.post("/")
def add_company(payload: CompanyCreateSchema,
                db: Session = Depends(get_db),
                token: str = Depends(JWTBearer())):
    new_company = company_service.add_company(db, payload,
                                                    get_data_from_token(token))
    return {"success": True, "user_id": new_company.id}


@router.put("/{companyId}")
def update_company(companyId: int,
                         payload: CompanyUpdateSchema,
                         db: Session = Depends(get_db),
                         token: str = Depends(JWTBearer())):
    company = company_service.update_company(db, companyId, payload,
                                                   get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}")
def delete_company(companyId: int,
                         db: Session = Depends(get_db),
                         token: str = Depends(JWTBearer())):
    company = company_service.delete_company(db, companyId,
                                                   get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}

# TODO: check
# #################################################################
@router.get("/{companyId}/users", response_model=List[CompanyUserGetSchema])
def get_company_users(companyId: int,
                            db: Session = Depends(get_db),
                            str=Depends(JWTBearer())):
    return company_service.get_company_users(db, companyId,
                                                   get_data_from_token(str))


@router.post("/{companyId}/users/{userId}")
def add_company_user(companyId: int,
                           userId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    company = company_service.add_company_user(
        db, companyId, userId, get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}/users/{userId}")
def delete_company_user(companyId: int,
                              userId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    company = company_service.delete_company_user(
        db, companyId, userId, get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}

#####################################################################################
@router.get("/{companyId}/events", response_model=EventGetSchema)
def get_company_events(companyId: int,
                             response: Response,
                             db: Session = Depends(get_db),
                             str=Depends(JWTBearer())):
    return company_service.get_company_events(db, companyId)
