from models.Company import CompanyUser as ModelCompanyUser
from models import TokenData
from models.UserType import UserType
from schemas.Company import CompanyUser as SchemaCompanyUser
from schemas.Company import CompanyUserUpdate as SchemaCompanyUserUpdate

from sqlalchemy.orm import Session

from security import get_password_hash
from utils.service_utils import set_existing_data, check_image

from errors.AuthenticationException import AuthenticationException
from errors.NotFoundException import NotFoundException
from errors.ValidationException import ValidationException

async def get_all(db: Session):
    return db.query(ModelCompanyUser).all()


async def get_company_user(companyUserId: int, db: Session):
    user = db.query(ModelCompanyUser).filter(ModelCompanyUser.id == companyUserId).first()
    if user is None:
        raise NotFoundException("Company user not found")
    return user

async def add_company_user(payload: SchemaCompanyUser, db: Session):
    new_company_user = ModelCompanyUser(**payload.dict())
    new_company_user.password = get_password_hash(payload.password)
    payload = check_image(payload)
    db.add(new_company_user)
    db.commit()
    db.refresh(new_company_user)
    return new_company_user


async def update_company_user(payload: SchemaCompanyUserUpdate, companyUserId: int,
                              db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                      (data.type == "company_user"
                                       and data.user_id != companyUserId))):
            raise AuthenticationException("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if not company_user:
        raise NotFoundException("Company user not found")
    payload = check_image(payload)
    updated = set_existing_data(company_user, payload)
    if payload.password is not None:
        company_user.password = get_password_hash(payload.password)
    db.commit()
    db.refresh(company_user)
    return company_user, updated


async def delete_company_user(companyUserId: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                      (data.type == "company_user"
                                       and data.user_id != companyUserId))):
            raise AuthenticationException("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if not company_user:
        raise NotFoundException("Company user not found")
    db.delete(company_user)
    db.commit()
    return company_user
