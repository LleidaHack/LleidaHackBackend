from typing import List, Union
from fastapi import Depends, Response, APIRouter

from security import get_data_from_token
from utils.auth_bearer import JWTBearer

from src.Company.service import CompanyService

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

company_service = CompanyService()

@router.get("/all", response_model=List[CompanyGetSchema])
def get_companies():
    return company_service.get_all()


@router.get("/{companyId}",
            response_model=Union[CompanyGetSchema, CompanyGetAllSchema])
def get_company(companyId: int):
    return company_service.get_company(companyId)


@router.post("/")
def add_company(payload: CompanyCreateSchema,
                token: str = Depends(JWTBearer())):
    new_company = company_service.add_company(payload,
                                              get_data_from_token(token))
    return {"success": True, "user_id": new_company.id}


@router.put("/{companyId}")
def update_company(companyId: int,
                   payload: CompanyUpdateSchema,
                   token: str = Depends(JWTBearer())):
    company = company_service.update_company(companyId, payload,
                                             get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}")
def delete_company(companyId: int,
                   token: str = Depends(JWTBearer())):
    company = company_service.delete_company(companyId,
                                             get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}


# TODO: check
# #################################################################
@router.get("/{companyId}/users", response_model=List[CompanyUserGetSchema])
def get_company_users(companyId: int,
                      str=Depends(JWTBearer())):
    return company_service.get_company_users(companyId,
                                             get_data_from_token(str))


@router.post("/{companyId}/users/{userId}")
def add_company_user(companyId: int,
                     userId: int,
                     response: Response,
                     token: str = Depends(JWTBearer())):
    company = company_service.add_company_user(companyId, userId,
                                               get_data_from_token(token))
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}/users/{userId}")
def delete_company_user(companyId: int,
                        userId: int,
                        response: Response,
                        token: str = Depends(JWTBearer())):
    company = company_service.delete_company_user(companyId, userId,
                                                  get_data_from_token(token))
    return {"success": True, "deleted_id": company.id}


#####################################################################################
@router.get("/{companyId}/events", response_model=EventGetSchema)
def get_company_events(companyId: int,
                       response: Response,
                       str=Depends(JWTBearer())):
    return company_service.get_company_events(companyId)
