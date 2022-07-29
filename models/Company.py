from __future__ import annotations
from typing import List
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from models.User import User
from schemas.Event import Event

class Company(Base):
    __tablename__ = 'company'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    address: str = Column(String)
    telephone: str = Column(String)
    website: str = Column(String)
    logo: str = Column(String)
    users: List[CompanyUser] = relationship('CompanyUser', back_populates='company')
    events: List[Event] = relationship('Event', secondary='company_event_participation')

class CompanyUser(User):
    __tablename__ = 'company_user'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'), primary_key=True)
    company: Company = relationship('Company', back_populates='users')
    role: str = Column(String)
    image_id: str = Column(String)
    
    __mapper_args__ = {
        "polymorphic_identity": "company",
    }