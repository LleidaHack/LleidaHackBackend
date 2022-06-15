from datetime import date
from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

from models.Hacker import Hacker as ModelHacker
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.Company import Company as ModelCompany
from models.Hacker import HackerGroup as ModelHackerGroup


class HackerParticipation(Base):
    __tablename__ = "hacker_event_participation"
    user_id = Column(Integer, ForeignKey("hacker.user_id"), primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), primary_key=True, index=True)

class HackerGroupParticipation(Base):
    __tablename__ = "hacker_group_event_participation"
    user_id = Column(Integer, ForeignKey("hacker_group.id"), primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), primary_key=True, index=True)

class LleidaHackerParticipation(Base):
    __tablename__ = "lleida_hacker_event_participation"
    user_id = Column(Integer, ForeignKey("lleida_hacker.user_id"), primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), primary_key=True, index=True)

class CompanyParticipation(Base):
    __tablename__ = "company_event_participation"
    company_id = Column(Integer, ForeignKey("company.id"), primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), primary_key=True, index=True)

class Event(Base):
    __tablename__ = 'llhk_event'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    start_date: date = Column(DateTime, default=func.now())
    end_date: date = Column(DateTime, default=func.now())
    # start_time: Time = Column(Time, default=func.now())
    location: str = Column(String)
    archived: bool = Column(Boolean, default=False)
    status: int = Column(Integer, default=0)
    price: int = Column(Integer, default=0)
    max_participants: int = Column(Integer)
    max_sponsors: int = Column(Integer)
    
    participants: List[ModelHacker] = relationship('Hacker', secondary='hacker_event_participation')
    organizers: List[ModelLleidaHacker] = relationship("ModelHacker", secondary='lleida_hacker_event_participation')
    sponsors: List[ModelCompany] = relationship('Company', secondary='company_event_participation')
    groups: List[ModelHackerGroup] = relationship('HackerGroup', secondary='hacker_group_event_participation')
    # status: int = Column(Integer, default=0)
