from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.impl.Company.model import Company
from src.impl.User.model import User
from src.utils.UserType import UserType


class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    company_id = Column(Integer, ForeignKey(Company.id), primary_key=True)
    company = relationship('Company', back_populates='users')
    active: bool = (Column(Integer))
    role: str = (Column(String))
    accepted: bool = (Column(Boolean, default=False))
    rejected: bool = (Column(Boolean, default=False))

    __mapper_args__ = {
        "polymorphic_identity": UserType.COMPANYUSER.value,
    }
