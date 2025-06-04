from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.impl.User.model import User
from src.utils.UserType import UserType

if TYPE_CHECKING:
    from src.impl.Company.model import Company


class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id: Mapped[int] = mapped_column(ForeignKey('my_user.id'), primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey('company.id'), primary_key=True)
    company: Mapped["Company"] = relationship('Company', back_populates='users')
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    rejected: Mapped[bool] = mapped_column(Boolean, default=False)

    __mapper_args__ = {
        "polymorphic_identity": UserType.COMPANYUSER.value,
    }
