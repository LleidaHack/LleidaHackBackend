from fastapi_sqlalchemy import db

from src.error.AuthenticationError import AuthenticationError
from src.error.NotFoundError import NotFoundError
from src.impl.Company.model import Company
from src.impl.Company.schema import CompanyCreate, CompanyUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import check_image, set_existing_data
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class CompanyService(BaseService):
    name = 'company_service'
    user_service = None

    def get_all(self):
        return db.session.query(Company).all()

    def get_by_id(self, company_id: int):
        company = db.session.query(Company).filter(Company.id == company_id).first()
        if company is None:
            raise NotFoundError('company not found')
        return company

    def get_company(self, company_id: int):
        return self.get_by_id(company_id)

    def get_by_tier(self, tier: int):
        return db.session.query(Company).filter(Company.tier == tier).all()

    def add_company(self, payload: CompanyCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        # if data.user_type == UserType.COMPANYUSER.value:
        # user = self.user_service.get_by_id(data.user_id)
        payload = check_image(payload)
        new_company = Company(**payload.model_dump())
        db.session.add(new_company)
        db.session.commit()
        db.session.refresh(new_company)
        return new_company

    @BaseService.needs_service(user_service.UserService)
    def update_company(self, company_id: int, payload: CompanyUpdate, data: BaseToken):
        if not data.check([UserType.COMPANYUSER, UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        company = self.get_by_id(company_id)
        if data.user_type == UserType.COMPANYUSER.value:
            user = self.user_service.get_by_id(data.user_id)
            users = [user.id for user in company.users]
            if not (data.user_id in users and company.leader_id == user.id):
                raise AuthenticationError('Not authorized')
        if payload.image is not None:
            payload = check_image(payload)
        updated = set_existing_data(company, payload)
        db.session.commit()
        db.session.refresh(company)
        return company, updated

    def delete_company(self, company_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER]):
            raise AuthenticationError('Not authorized')
        company = self.get_by_id(company_id)
        users = [user.id for user in company.users]
        if not (
            data.is_admin
            or (data.user_id in users and company.leader_id == data.user_id)
        ):
            raise AuthenticationError('Not authorized')
        db.session.delete(company)
        db.session.commit()
        return company

    def get_company_users(self, company_id: int, data: BaseToken):
        company = self.get_by_id(company_id)
        return company.users

    @BaseService.needs_service(user_service.UserService)
    def add_company_user(self, company_id: int, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER]):
            raise AuthenticationError('Not authorized')
        company = self.get_by_id(company_id)
        users = [user.id for user in company.users]
        if (
            not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER])
            or data.user_id not in users
        ):
            raise AuthenticationError('Not authorized')
        user = self.user_service.get_by_id(user_id)
        company.users.append(user)
        db.session.commit()
        db.session.refresh(company)
        return company

    @BaseService.needs_service(user_service.UserService)
    def delete_company_user(self, company_id: int, user_id: int, data: BaseToken):
        if not data.check([UserType.COMPANYUSER, UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')
        company = self.get_by_id(company_id)
        users = [user.id for user in company.users]
        if not data.is_admin or data.user_id not in users:
            raise AuthenticationError('Not authorized')
        user = self.user_service.get_by_id(user_id)
        company.users.remove(user)
        db.session.commit()
        db.session.refresh(company)
        return company

    def get_company_events(self, company_id: int):
        company = self.get_by_id(company_id)
        return company.events
