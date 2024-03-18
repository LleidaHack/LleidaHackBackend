from datetime import datetime as date

from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.CompanyUser.model import CompanyUser as ModelCompanyUser
from src.impl.CompanyUser.schema import \
    CompanyUserCreate as CompanyUserCreateSchema
from src.impl.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.impl.CompanyUser.schema import \
    CompanyUserGetAll as CompanyUserGetAllSchema
from src.impl.CompanyUser.schema import \
    CompanyUserUpdate as CompanyUserUpdateSchema
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash
from src.utils.service_utils import (check_image, check_user,
                                     generate_user_code, set_existing_data)
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class CompanyUserService(BaseService):
    name = 'companyuser_service'

    def get_all(self):
        return db.session.query(ModelCompanyUser).all()

    def get_by_id(self, companyUserId: int):
        user = db.session.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == companyUserId).first()
        if user is None:
            raise NotFoundException("Company user not found")
        return user

    def get_company_user(self, companyUserId: int, data: BaseToken):
        user = self.get_by_id(companyUserId)
        if data.check([UserType.LLEIDAHACKER.value, UserType.COMPANYUSER],
                      companyUserId):
            return CompanyUserGetAllSchema.from_orm(user)
        return CompanyUserGetSchema.from_orm(user)

    def add_company_user(self, payload: CompanyUserCreateSchema):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_company_user = ModelCompanyUser(**payload.dict(),
                                            code=generate_user_code())
        new_company_user.password = get_password_hash(payload.password)
        if payload.image is not None:
            payload = check_image(payload)
        db.session.add(new_company_user)
        db.session.commit()
        db.session.refresh(new_company_user)
        return new_company_user

    def update_company_user(self, payload: CompanyUserUpdateSchema,
                            companyUserId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER
                           ]) or data.user_id != companyUserId:
            raise AuthenticationException("Not authorized")
        company_user = self.get_by_id(companyUserId)
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(company_user, payload)
        company_user.updated_at = date.now()
        updated.append("updated_at")
        if payload.password is not None:
            company_user.password = get_password_hash(payload.password)
            updated.append("password")
        db.session.commit()
        db.session.refresh(company_user)
        return company_user, updated

    def delete_company_user(self, companyUserId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER
                           ]) or data.user_id != companyUserId:
            raise AuthenticationException("Not authorized")
        company_user = self.get_by_id(companyUserId)
        db.session.delete(company_user)
        db.session.commit()
        return company_user
