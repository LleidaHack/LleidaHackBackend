from fastapi_sqlalchemy import db

import src.impl.User.service as U_S
from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.Company.model import Company
from src.impl.Company.schema import CompanyCreate
from src.impl.Company.schema import CompanyUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import check_image, set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class CompanyService(BaseService):
    name = 'company_service'
    user_service = None

    def get_all(self):
        return db.session.query(Company).all()

    def get_by_id(self, companyId: int):
        company = db.session.query(Company).filter(
            Company.id == companyId).first()
        if company is None:
            raise NotFoundException('company not found')
        return company

    def get_company(self, companyId: int):
        return self.get_by_id(companyId)
    
    def get_by_tier(self, tier: int):
        companies = db.session.query(ModelCompany).filter(
            ModelCompany.tier == tier
        )
        return companies

    def add_company(self, payload: CompanyCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        # if data.user_type == UserType.COMPANYUSER.value:
        # user = self.user_service.get_by_id(data.user_id)
        payload = check_image(payload)
        new_company = Company(**payload.model_dump())
        db.session.add(new_company)
        db.session.commit()
        db.session.refresh(new_company)
        return new_company

    @BaseService.needs_service(U_S.UserService)
    def update_company(self, companyId: int, payload: CompanyUpdate,
                       data: BaseToken):
        if not data.check([UserType.COMPANYUSER, UserType.LLEIDAHACKER]):
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
        db.session.commit()
        db.session.refresh(company)
        return company, updated

    def delete_company(self, companyId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER]):
            raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not (data.is_admin or
                (data.user_id in users and company.leader_id == data.user_id)):
            raise AuthenticationException(f"Not authorized")
        db.session.delete(company)
        db.session.commit()
        return company

    def get_company_users(self, companyId: int, data: BaseToken):
        company = self.get_by_id(companyId)
        return company.users

    @BaseService.needs_service(U_S.UserService)
    def add_company_user(self, companyId: int, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER]):
            raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not data.check([UserType.LLEIDAHACKER, UserType.COMPANYUSER
                           ]) or data.user_id not in users:
            raise AuthenticationException("Not authorized")
        user = self.user_service.get_by_id(userId)
        company.users.append(user)
        db.session.commit()
        db.session.refresh(company)
        return company

    @BaseService.needs_service(U_S.UserService)
    def delete_company_user(self, companyId: int, userId: int,
                            data: BaseToken):
        if not data.check([UserType.COMPANYUSER, UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        company = self.get_by_id(companyId)
        users = [user.id for user in company.users]
        if not data.is_admin or data.user_id not in users:
            raise AuthenticationException("Not authorized")
        user = self.user_service.get_by_id(userId)
        company.users.remove(user)
        db.session.commit()
        db.session.refresh(company)
        return company

    def get_company_events(self, companyId: int):
        company = self.get_by_id(companyId)
        return company.events
