from models.User import User as ModelUser
from models.Company import Company as ModelCompany
from models.TokenData import TokenData
from models.UserType import UserType

from schemas.Company import Company as SchemaCompany
from schemas.Company import CompanyUpdate as SchemaCompanyUpdate
# from schemas.Company import CompanyUser as SchemaCompanyUser

from sqlalchemy.orm import Session

from utils.service_utils import set_existing_data, check_image

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException


async def get_all(db: Session):
    return db.query(ModelCompany).all()


async def get_company(db: Session, companyId: int):
    return db.query(ModelCompany).filter(ModelCompany.id == companyId).first()


async def add_company(db: Session, payload: SchemaCompany, data: TokenData):
    if not data.is_admin:
        if not (data.available
                and data.user_type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if data.user_type == UserType.COMPANYUSER.value:
        user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
        if user is None:
            raise NotFoundException("User not found")
    payload = check_image(payload)
    new_company = ModelCompany(**payload.dict())
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


async def update_company(db: Session, companyId: int,
                         payload: SchemaCompanyUpdate, data: TokenData):
    if not data.is_admin:
        if not (data.available and
                (data.user_type == UserType.COMPANYUSER.value
                 or data.user_type == UserType.LLEIDAHACKER.value)):
            raise AuthenticationException("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise NotFoundException("Company not found")
    if data.user_type == UserType.COMPANYUSER.value:
        user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
        users = [user.id for user in company.users]
        if not (data.user_id in users and company.leader_id == user.id):
            raise AuthenticationException("Not authorized")
    if payload.image is not None:
        payload = check_image(payload)
    updated = set_existing_data(company, payload)
    db.commit()
    db.refresh(company)
    return company, updated


async def delete_company(db: Session, companyId: int, data: TokenData):
    if not data.is_admin:
        if not (data.available and
                (data.user_type == UserType.LLEIDAHACKER.value
                 or data.user_type == UserType.COMPANYUSER.value)):
            raise AuthenticationException("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise NotFoundException("Company not found")
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not (data.user_id in users and company.leader_id == data.user_id):
            raise AuthenticationException("Not authorized")
    db.delete(company)
    db.commit()
    return company


async def get_company_users(db: Session, companyId: int, data: TokenData):
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise NotFoundException("Company not found")
    return company.users


async def add_company_user(db: Session, companyId: int, userId: int,
                           data: TokenData):
    if not data.is_admin:
        if not (data.available and
                (data.user_type == UserType.LLEIDAHACKER.value
                 or data.user_type == UserType.COMPANYUSER.value)):
            raise AuthenticationException("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise NotFoundException("Company not found")
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not (data.user_type == UserType.LLEIDAHACKER.value or
                (data.user_type == UserType.COMPANYUSER.value
                 and data.user_id in users)):
            raise AuthenticationException("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    if user is None:
        raise NotFoundException("User not found")
    company.users.append(user)
    db.commit()
    db.refresh(company)
    return company


async def delete_company_user(db: Session, companyId: int, userId: int,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and
                (data.user_type == UserType.COMPANYUSER.value
                 or data.user_type == UserType.LLEIDAHACKER.value)):
            raise AuthenticationException("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    users = [user.id for user in company.users]
    if not data.is_admin:
        if not data.user_id in users:
            raise AuthenticationException("Not authorized")
    if company is None:
        raise NotFoundException("Company not found")
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    company.users.remove(user)
    db.commit()
    db.refresh(company)
    return company


async def get_company_events(db: Session, companyId: int):
    company = db.query(ModelCompany).filter(
        ModelCompany.id == companyId).first()
    if company is None:
        raise NotFoundException("Company not found")
    return company.events
