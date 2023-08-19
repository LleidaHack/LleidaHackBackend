from models.User import User as ModelUser
from models.Company import Company as ModelCompany
from models.TokenData import TokenData

from schemas.Company import Company as SchemaCompany
from schemas.Company import CompanyUser as SchemaCompanyUser

from sqlalchemy.orm import Session

from utils.service_utils import set_existing_data

async def get_all(db: Session):
    return db.query(ModelCompany).all()


async def get_company(db: Session, companyId: int):
    return db.query(ModelCompany).filter(ModelCompany.id == companyId).first()


async def add_company(db: Session, payload: SchemaCompany, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.user_type == "company_user"
                                      or data.user_type == "lleida_hacker"):
            raise Exception("Not authorized")
    if data.user_type == "company_user":
        user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
    new_company = ModelCompany(**payload.dict())
    if data.user_type == "company_user":
        new_company.users.append(user)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


async def update_company(db: Session, companyId: int, payload: SchemaCompany,
                         data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.user_type == "company_user"
                                      or data.user_type == "lleida_hacker"):
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise Exception("Company not found")
    if data.user_type == "company_user":
        user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
        users = [user.id for user in company.users]
        if not data.user_id in users or company.leader_id != user.id:
            raise Exception("Not authorized")
    set_existing_data(company, payload)
    db.commit()
    db.refresh(company)
    return company


async def delete_company(db: Session, companyId: int, data: TokenData):
    if not data.is_admin:
        if not data.available or not data.user_type == "company_user":
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise Exception("Company not found")
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not data.user_id in users:
            raise Exception("Not authorized")
    db.delete(company)
    db.commit()
    return company


async def get_company_users(db: Session, companyId: int, data: TokenData):
    if not data.is_admin:
        if not data.available or not data.user_type == "company_user":
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise Exception("Company not found")
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not data.user_id in users:
            raise Exception("Not authorized")
    return company.users


async def add_company_user(db: Session, companyId: int, userId: int,
                           data: TokenData):
    if not data.is_admin:
        if not data.available or not data.user_type == "company_user":
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise Exception("Company not found")
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not data.user_id in users:
            raise Exception("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    if user is None:
        raise Exception("User not found")
    company.users.append(user)
    db.commit()
    db.refresh(company)
    return company


async def delete_company_user(db: Session, companyId: int, userId: int,
                              data: TokenData):
    if not data.is_admin:
        if not data.available or not data.user_type == "company_user":
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not data.user_id in users:
            raise Exception("Not authorized")
    if company is None:
        raise Exception("Company not found")
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    company.users.remove(user)
    db.commit()
    db.refresh(company)
    return company


async def get_company_events(db: Session, companyId: int):
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise Exception("Company not found")
    return company.events
