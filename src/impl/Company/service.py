from src.utils.UserType import UserType
from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data, check_image
from src.impl.User.service import UserService

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.impl.User.model import User as ModelUser
from src.impl.Company.model import Company as ModelCompany

from src.impl.Company.schema import CompanyCreate as CompanyCreateSchema
from src.impl.Company.schema import CompanyUpdate as CompanyUpdateSchema
from src.utils.Token import BaseToken


class CompanyService(BaseService):

    user_service = UserService()

    def get_all(self):
        return self.db.query(ModelCompany).all()
    
    def get_by_id(self, companyId: int):
        company =  self.db.query(ModelCompany).filter(ModelCompany.id == companyId).first()
        if company is None:
            raise NotFoundException('company not found')
        return company
    def get_company(self, companyId: int):
        return self.db.query(ModelCompany).filter(
            ModelCompany.id == companyId).first()

    def add_company(self, payload: CompanyCreateSchema, data: BaseToken):
        if not data.is_admin:
            if not (data.available
                    and data.user_type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        # if data.user_type == UserType.COMPANYUSER.value:
            # user = self.user_service.get_by_id(data.user_id)
        payload = check_image(payload)
        new_company = ModelCompany(**payload.dict())
        self.db.add(new_company)
        self.db.commit()
        self.db.refresh(new_company)
        return new_company

    def update_company(self, companyId: int, payload: CompanyUpdateSchema,
                       data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.user_type == UserType.COMPANYUSER.value
                     or data.user_type == UserType.LLEIDAHACKER.value)):
                raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        if data.user_type == UserType.COMPANYUSER.value:
            user = self.user_service.get_by_id(data.user_id)
            users = [user.id for user in company.users]
            if not (data.user_id in users and company.leader_id == user.id):
                raise AuthenticationException("Not authorized")
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(company, payload)
        self.db.commit()
        self.db.refresh(company)
        return company, updated

    def delete_company(self, companyId: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.user_type == UserType.LLEIDAHACKER.value
                     or data.user_type == UserType.COMPANYUSER.value)):
                raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not data.is_admin:
            if not (data.user_id in users
                    and company.leader_id == data.user_id):
                raise AuthenticationException("Not authorized")
        self.db.delete(company)
        self.db.commit()
        return company

    def get_company_users(self, companyId: int, data: BaseToken):
        company = self.get_by_id(companyId)
        return company.users

    def add_company_user(self, companyId: int, userId: int, data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.user_type == UserType.LLEIDAHACKER.value
                     or data.user_type == UserType.COMPANYUSER.value)):
                raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not data.is_admin:
            if not (data.user_type == UserType.LLEIDAHACKER.value or
                    (data.user_type == UserType.COMPANYUSER.value
                     and data.user_id in users)):
                raise AuthenticationException("Not authorized")
        user = self.user_service.get_by_id(userId)
        company.users.append(user)
        self.db.commit()
        self.db.refresh(company)
        return company

    def delete_company_user(self, companyId: int, userId: int,
                            data: BaseToken):
        if not data.is_admin:
            if not (data.available and
                    (data.user_type == UserType.COMPANYUSER.value
                     or data.user_type == UserType.LLEIDAHACKER.value)):
                raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not data.is_admin:
            if not data.user_id in users:
                raise AuthenticationException("Not authorized")
        if company is None:
            raise NotFoundException("Company not found")
        user = self.user_service.get_by_id(userId)
        company.users.remove(user)
        self.db.commit()
        self.db.refresh(company)
        return company

    def get_company_events(self, companyId: int):
        company = self.get_by_id(companyId)
        return company.events
