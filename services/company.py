from models.User import User as ModelUser
from models.Company import Company as ModelCompany

from schemas.Company import Company as SchemaCompany
from schemas.Company import CompanyUser as SchemaCompanyUser

from sqlalchemy.orm import Session

async def get_all(db: Session):
    return db.query(ModelCompany).all()

async def get_company(db: Session, companyId: int):
    return db.query(ModelCompany).filter(ModelCompany.id == companyId).first()

async def add_company(db: Session, payload: SchemaCompany):
    new_company = ModelCompany(name=payload.name, 
                               description=payload.description,
                               website=payload.website,
                               telephone=payload.telephone,
                               address=payload.address,
                               logo=payload.logo,
    )
    db.add(new_company)
    db.commit()
    return new_company

async def update_company(db: Session, companyId: int, payload: SchemaCompany):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    company.name = payload.name
    company.description = payload.description
    company.website = payload.website
    company.telephone = payload.telephone
    company.address = payload.address
    company.logo = payload.logo
    db.commit()
    db.refresh(company)
    return company

async def delete_company(db: Session, companyId: int):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    db.delete(company)
    db.commit()
    return company

async def get_company_users(db: Session, companyId: int):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    return company.users

async def add_company_user(db: Session, companyId: int, payload: SchemaCompanyUser):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    user = db.query(ModelUser).filter(ModelUser.id == payload.user_id).first()
    company.users.append(user)
    db.commit()
    db.refresh(company)
    return company

async def delete_company_user(db: Session, companyId: int, userId: int):
    company = db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    company.users.remove(user)
    db.commit()
    db.refresh(company)
    return company
