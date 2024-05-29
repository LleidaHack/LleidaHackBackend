# from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from src.impl.User.model import User
from src.utils.UserType import UserType
if TYPE_CHECKING:
    from src.impl.Company.model import Company


class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id: int = Field(foreign_key = 'my_user.id', primary_key=True)
    company_id: int = Field(foreign_key = 'company.id', primary_key=True)
    company: 'Company' = Relationship(back_populates='users')
    active: bool = Field(default=True)
    role: str
    accepted: bool = Field(default=False)
    rejected: bool = Field(default=False)

    __mapper_args__ = {
        "polymorphic_identity": UserType.COMPANYUSER.value,
    }

