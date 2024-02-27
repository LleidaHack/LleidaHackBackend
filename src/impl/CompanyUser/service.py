from datetime import datetime as date
from pydantic import parse_obj_as

from src.utils.security import get_password_hash
from src.utils.UserType import UserType
from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data, check_image, generate_user_code, check_user
from src.utils.Token import BaseToken


from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.impl.CompanyUser.schema import CompanyUserCreate as CompanyUserCreateSchema
from src.impl.CompanyUser.schema import CompanyUserUpdate as CompanyUserUpdateSchema
from src.impl.CompanyUser.schema import CompanyUserGet as CompanyUserGetSchema
from src.impl.CompanyUser.schema import CompanyUserGetAll as CompanyUserGetAllSchema
from src.impl.CompanyUser.model import CompanyUser as ModelCompanyUser


class CompanyUserService(BaseService):

    def get_all(self):
        return self.db.query(ModelCompanyUser).all()

    def get_company_user(self, companyUserId: int, data: BaseToken):
        user = self.db.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == companyUserId).first()
        if user is None:
            raise NotFoundException("Company user not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value or
                              (data.type == UserType.COMPANYUSER.value
                               and data.user_id == companyUserId))):
            return parse_obj_as(CompanyUserGetAllSchema, user)
        return parse_obj_as(CompanyUserGetSchema, user)

    def add_company_user(self, payload: CompanyUserCreateSchema):
        check_user(payload.email, payload.nickname, payload.telephone)
        new_company_user = ModelCompanyUser(**payload.dict(),
                                            code=generate_user_code())
        new_company_user.password = get_password_hash(payload.password)
        if payload.image is not None:
            payload = check_image(payload)
        self.db.add(new_company_user)
        self.db.commit()
        self.db.refresh(new_company_user)
        return new_company_user

    def update_company_user(self, payload: CompanyUserUpdateSchema,
                            companyUserId: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value or
                     (data.type == UserType.COMPANYUSER.value
                      and data.user_id != companyUserId))):
                raise AuthenticationException("Not authorized")
        company_user = self.db.query(ModelCompanyUser).filter(
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
        self.db.commit()
        self.db.refresh(company_user)
        return company_user, updated

    def delete_company_user(self, companyUserId: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.type == UserType.LLEIDAHACKER.value or
                     (data.type == UserType.COMPANYUSER.value
                      and data.user_id != companyUserId))):
                raise AuthenticationException("Not authorized")
        company_user = self.db.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == companyUserId).first()
        if not company_user:
            raise NotFoundException("Company user not found")
        self.db.delete(company_user)
        self.db.commit()
        return company_user
