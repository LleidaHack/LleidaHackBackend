from datetime import datetime as date
from src.Company.model import CompanyUser as ModelCompanyUser
from src.Utils import TokenData
from src.Utils.UserType import UserType
from src.Company.schema import CompanyUser as SchemaCompanyUser
from src.Company.schema import CompanyUserUpdate as SchemaCompanyUserUpdate

from sqlalchemy.orm import Session

from security import get_password_hash
from utils.service_utils import set_existing_data, check_image, generate_user_code

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException

from utils.hide_utils import companyuser_show_private
from utils.service_utils import check_user


async def get_all(db: Session):
    return db.query(ModelCompanyUser).all()


async def get_company_user(companyUserId: int, db: Session, data: TokenData):
    user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if user is None:
        raise NotFoundException("Company user not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value or
                          (data.type == UserType.COMPANYUSER.value
                           and data.user_id == companyUserId))):
        companyuser_show_private(user)
    return user


async def add_company_user(payload: SchemaCompanyUser, db: Session):
    check_user(db, payload.email, payload.nickname, payload.telephone)
    new_company_user = ModelCompanyUser(**payload.dict(),
                                        code=generate_user_code(db))
    new_company_user.password = get_password_hash(payload.password)
    if payload.image is not None:
        payload = check_image(payload)
    db.add(new_company_user)
    db.commit()
    db.refresh(new_company_user)
    return new_company_user


async def update_company_user(payload: SchemaCompanyUserUpdate,
                              companyUserId: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.COMPANYUSER.value
                                     and data.user_id != companyUserId))):
            raise AuthenticationException("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if not company_user:
        raise NotFoundException("Company user not found")
    if payload.image is not None:
        payload = check_image(payload)
    updated = set_existing_data(company_user, payload)
    company_user.updated_at = date.now()
    updated.append("updated_at")
    if payload.password is not None:
        company_user.password = get_password_hash(payload.password)
        updated.append("password")
    db.commit()
    db.refresh(company_user)
    return company_user, updated


async def delete_company_user(companyUserId: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.COMPANYUSER.value
                                     and data.user_id != companyUserId))):
            raise AuthenticationException("Not authorized")
    company_user = db.query(ModelCompanyUser).filter(
        ModelCompanyUser.id == companyUserId).first()
    if not company_user:
        raise NotFoundException("Company user not found")
    db.delete(company_user)
    db.commit()
    return company_user
