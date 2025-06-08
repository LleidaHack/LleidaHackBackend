from datetime import datetime as date

from fastapi_sqlalchemy import db

from src.error.AuthenticationError import AuthenticationError
from src.error.NotFoundError import NotFoundError
from src.impl.CompanyUser.model import CompanyUser
from src.impl.CompanyUser.schema import (
    CompanyUserCreate,
    CompanyUserGet,
    CompanyUserGetAll,
    CompanyUserUpdate,
)
from src.impl.UserConfig.model import UserConfig
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash
from src.utils.service_utils import (
    check_image,
    check_user,
    generate_user_code,
    set_existing_data,
)
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class CompanyUserService(BaseService):
    name = 'companyuser_service'

    def get_all(self):
        return db.session.query(CompanyUser).all()

    def get_by_id(self, company_user_id: int):
        user = (
            db.session.query(CompanyUser)
            .filter(CompanyUser.id == company_user_id)
            .first()
        )
        if user is None:
            raise NotFoundError('Company user not found')
        return user

    def get_company_user(self, company_user_id: int, data: BaseToken):
        user = self.get_by_id(company_user_id)
        if data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER], company_user_id):
            return CompanyUserGetAll.model_validate(user)
        return CompanyUserGet.model_validate(user)

    def add_company_user(self, payload: CompanyUserCreate):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_company_user = CompanyUser(
            **payload.model_dump(exclude={'config'}), code=generate_user_code()
        )
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

    def update_company_user(
        self, payload: CompanyUserUpdate, company_user_id: int, data: BaseToken
    ):
        if (
            not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER])
            or data.user_id != company_user_id
        ):
            raise AuthenticationError('Not authorized')
        company_user = self.get_by_id(company_user_id)
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(company_user, payload)
        company_user.updated_at = date.now()
        updated.append('updated_at')
        if payload.password is not None:
            company_user.password = get_password_hash(payload.password)
            updated.append('password')
        db.session.commit()
        db.session.refresh(company_user)
        return company_user, updated

    def delete_company_user(self, company_user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]) and not data.check(
            [UserType.COMPANYUSER], company_user_id
        ):
            raise AuthenticationError('Not authorized')
        company_user = self.get_by_id(company_user_id)
        db.session.delete(company_user)
        db.session.commit()
        return company_user
