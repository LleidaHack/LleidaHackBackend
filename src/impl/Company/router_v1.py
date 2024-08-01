from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Company.schema import CompanyCreate as CompanyCreateSchema
from src.impl.Company.schema import CompanyGet as CompanyGetSchema
from src.impl.Company.schema import CompanyGetAll as CompanyGetAllSchema
from src.impl.Company.schema import CompanyUpdate as CompanyUpdateSchema
from src.impl.Company.service import CompanyService
from src.impl.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)

company_service = CompanyService()


@router.get("/all", response_model=List[CompanyGetSchema])
def get_all():
    return company_service.get_all()


@router.post("/")
def add(payload: CompanyCreateSchema, token: BaseToken = Depends(JWTBearer())):
    new_company = company_service.add_company(payload, token)
    return {"success": True, "id": new_company.id}


@router.get("/{companyId}",
            response_model=Union[CompanyGetAllSchema, CompanyGetSchema])
def get(companyId: int):
    return company_service.get_company(companyId)


@router.put("/{companyId}")
def update(companyId: int,
           payload: CompanyUpdateSchema,
           token: BaseToken = Depends(JWTBearer())):
    company, updated = company_service.update_company(companyId, payload,
                                                      token)
    return {"success": True, "updated_id": company.id, 'updated': updated}


@router.delete("/{companyId}")
def delete(companyId: int, token: BaseToken = Depends(JWTBearer())):
    company = company_service.delete_company(companyId, token)
    return {"success": True, "deleted_id": company.id}


# TODO: check
# #################################################################
@router.get("/{companyId}/users", response_model=List[CompanyUserGetSchema])
def get_users(companyId: int, token: BaseToken = Depends(JWTBearer())):
    return company_service.get_company_users(companyId, token)


@router.post("/{companyId}/users/{userId}")
def add_user(companyId: int,
             userId: int,
             token: BaseToken = Depends(JWTBearer())):
    company = company_service.add_company_user(companyId, userId, token)
    return {"success": True, "updated_id": company.id}


@router.delete("/{companyId}/users/{userId}")
def delete_user(companyId: int,
                userId: int,
                token: BaseToken = Depends(JWTBearer())):
    company = company_service.delete_company_user(companyId, userId, token)
    return {"success": True, "deleted_id": company.id}


#####################################################################################
@router.get("/{companyId}/events", response_model=EventGetSchema)
def get_events(companyId: int, token: BaseToken = Depends(JWTBearer())):
    return company_service.get_company_events(companyId)
