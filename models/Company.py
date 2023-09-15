from __future__ import annotations
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from models.User import User
from models.UserType import UserType
from schemas.Event import Event

from sqlalchemy.orm import deferred
from sqlalchemy.orm import Mapped

class Company(Base):
    __tablename__ = 'company'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    address: str = Column(String)
    telephone: str = Column(String)
    website: str = Column(String)
    image: str = Column(String)
    is_image_url: bool = Column(Boolean, default=False)
    linkdin: str = Column(String)
    leader_id: int = Column(Integer, ForeignKey('user.id'))
    users = relationship('User', secondary='company_user')
    events = relationship('Event', secondary='company_event_participation')


class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'), primary_key=True)
    company = relationship('Company', back_populates='users')
    active: Mapped[bool] = deferred(Column(Integer))
    role: Mapped[str] = deferred(Column(String))
    accepted: Mapped[bool] = deferred(Column(Boolean, default=False))
    rejected: Mapped[bool] = deferred(Column(Boolean, default=False))

    __mapper_args__ = {
        "polymorphic_identity": UserType.COMPANYUSER.value,
    }
