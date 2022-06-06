from models.User import User as ModelUser
from models.Company import Company as ModelCompany
from models.Company import CompanyUser as ModelCompanyUser

from schemas.Company import Company as SchemaCompany
from schemas.Company import CompanyUser as SchemaCompanyUser

from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

router = APIRouter(
    prefix="/company",
    tags=["Company"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

@router.get("/all")
async def get_companies(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelCompany).all()

@router.get("/{companyId}")
async def get_company(companyId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelCompany).filter(ModelCompany.id == companyId).first()

@router.post("/")
async def add_company(payload:SchemaCompany, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_company = ModelCompany(name=payload.name, 
                               description=payload.description,
                               website=payload.website,
                               telephone=payload.telephone,
                               address=payload.address,
                               logo=payload.logo,
    )
    db.add(new_company)
    db.commit()
    return {"success": True, "created_id": new_company.id}

@router.put("/{companyId}")
async def update_company(companyId: int, payload: SchemaCompany, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    company.name = payload.name
    company.description = payload.description
    company.website = payload.Website
    company.telephone = payload.telephone
    company.address = payload.address
    company.logo = payload.logo
    db.commit()

@router.delete("/{companyId}")
async def delete_company(companyId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    db.delete(company)
    db.commit()

@router.get("/{companyId}/users")
async def get_company_users(companyId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return db.query(ModelCompanyUser).filter(ModelCompanyUser.company_id == companyId).all()

@router.post("/{companyId}/users/add")
async def add_company_user(companyId: int, payload: SchemaCompanyUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_company_user = ModelCompanyUser(company_id=companyId, user_id=payload.user_id, role=payload.role)
    db.add(new_company_user)
    db.commit()
    return {"success": True, "created_id": new_company_user.id}

@router.delete("/{companyId}/users/{userId}")
async def delete_company_user(companyId: int, userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    company_user = db.query(ModelCompanyUser).filter(ModelCompanyUser.company_id == companyId, ModelCompanyUser.user_id == userId).first()
    db.delete(company_user)
    db.commit()
