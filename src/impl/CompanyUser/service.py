from datetime import datetime as date

from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.CompanyUser.model import CompanyUser
from src.impl.CompanyUser.schema import CompanyUserCreate
from src.impl.CompanyUser.schema import CompanyUserGet
from src.impl.CompanyUser.schema import CompanyUserGetAll
from src.impl.CompanyUser.schema import CompanyUserUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash
from src.utils.service_utils import (check_image, check_user,
                                     generate_user_code, set_existing_data)
from src.utils.Token import BaseToken
from src.utils.UserType import UserType
from src.impl.UserConfig.model import UserConfig


class CompanyUserService(BaseService):
    name = 'companyuser_service'

    def get_all(self):
        return db.session.query(CompanyUser).all()

    def get_by_id(self, companyUserId: int):
        user = db.session.query(CompanyUser).filter(
            CompanyUser.id == companyUserId).first()
        if user is None:
            raise NotFoundException("Company user not found")
        return user

    def get_company_user(self, companyUserId: int, data: BaseToken):
        user = self.get_by_id(companyUserId)
        if data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER],
                      companyUserId):
            return CompanyUserGetAll.model_validate(user)
        return CompanyUserGet.model_validate(user)

    def add_company_user(self, payload: CompanyUserCreate):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_company_user = CompanyUser(**payload.model_dump(exclude={"config"}),
                                            code=generate_user_code())
        new_company_user.password = get_password_hash(payload.password)
        new_company_user.active = True
        if payload.image is not None:
            payload = check_image(payload)

        new_config = UserConfig(**payload.config.model_dump())

        db.session.add(new_config)
        db.session.flush()
        new_company_user.config_id = new_config.id
        db.session.add(new_company_user)
        db.session.commit()
        db.session.refresh(new_company_user)
        return new_company_user

    def update_company_user(self, payload: CompanyUserUpdate,
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
        if not data.check([UserType.LLEIDAHACKER]) or not data.check(
            [UserType.COMPANYUSER], companyUserId):
            raise AuthenticationException("Not authorized")
        company_user = self.get_by_id(companyUserId)
        db.session.delete(company_user)
        db.session.commit()
        return company_user
