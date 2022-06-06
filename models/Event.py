from datetime import date
from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

from models.Hacker import ModelHacker
from models.LleidaHacker import ModelLleidaHacker
from models.Company import ModelCompany

class HackerParticipation(Base):
    __tablename__ = "hacker_event_participation"
    user_id = Column(Integer, ForeignKey("hacker.id"), index=True)
    event_id = Column(Integer, ForeignKey("event.id"), index=True)

class LleidaHackerParticipation(Base):
    __tablename__ = "lleida_hacker_event_participation"
    user_id = Column(Integer, ForeignKey("lleida_hacker.id"), index=True)
    event_id = Column(Integer, ForeignKey("event.id"), index=True)

class CompanyParticipation(Base):
    __tablename__ = "company_event_participation"
    company_id = Column(Integer, ForeignKey("company.id"), index=True)
    event_id = Column(Integer, ForeignKey("event.id"), index=True)

class Event(Base):
    __tablename__ = 'llhk_event'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    date: date = Column(DateTime, default=func.now())
    location: str = Column(String)
    archived: bool = Column(Boolean, default=False)
    
    participants: List[ModelHacker] = relationship('Hacker', secondary='hacker_event_participation')
    organizers: List[ModelLleidaHacker] = relationship("ModelHacker", secondary='lleida_hacker_event_participation')
    sponsors: List[ModelCompany] = relationship('Company', secondary='company_event_participation')
    # status: int = Column(Integer, default=0)
