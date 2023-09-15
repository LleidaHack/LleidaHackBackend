from datetime import date
from typing import List

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

from models.Hacker import Hacker as ModelHacker
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.Company import Company as ModelCompany
from models.Hacker import HackerGroup as ModelHackerGroup
from models.Meal import Meal as ModelMeal


class HackerParticipation(Base):
    __tablename__ = "hacker_event_participation"
    user_id = Column(Integer,
                     ForeignKey("hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class HackerRegistration(Base):
    __tablename__ = "hacker_event_registration"
    user_id = Column(Integer,
                     ForeignKey("hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)
    shirt_size: str = Column(String)
    food_restrictions: str = Column(String)
    cv: str = Column(String, default="")
    description: str = Column(String, default="")
    github: str = Column(String, default="")
    linkedin: str = Column(String, default="")
    dailyhack_url: str = Column(String, default="")
    update_user: bool = Column(Boolean, default=True)
    # accepted: bool = Column(Boolean, default=False)


class HackerAccepted(Base):
    __tablename__ = "hacker_event_accepted"
    user_id = Column(Integer,
                     ForeignKey("hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)
    # accepted: bool = Column(Boolean, default=False)


class HackerRejected(Base):
    __tablename__ = "hacker_event_rejected"
    user_id = Column(Integer,
                     ForeignKey("hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)
    # accepted: bool = Column(Boolean, default=False)


class LleidaHackerParticipation(Base):
    __tablename__ = "lleida_hacker_event_participation"
    user_id = Column(Integer,
                     ForeignKey("lleida_hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class CompanyParticipation(Base):
    __tablename__ = "company_event_participation"
    company_id = Column(Integer,
                        ForeignKey("company.id"),
                        primary_key=True,
                        index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class Event(Base):
    __tablename__ = 'event'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    start_date: date = Column(DateTime, default=func.now())
    end_date: date = Column(DateTime, default=func.now())
    max_group_size: int = Column(Integer)
    # start_time: Time = Column(Time, default=func.now())
    location: str = Column(String)
    archived: bool = Column(Boolean, default=False)
    status: int = Column(Integer, default=0)
    price: int = Column(Integer, default=0)
    max_participants: int = Column(Integer)
    max_sponsors: int = Column(Integer)
    image: str = Column(String)
    is_image_url: bool = Column(Boolean, default=False)
    is_open: bool = Column(Boolean, default=True)

    #TODO add registered_hackers
    registered_hackers = relationship('Hacker',
                                      secondary='hacker_event_registration')
    accepted_hackers = relationship('Hacker',
                                    secondary='hacker_event_accepted')
    rejected_hackers = relationship('Hacker',
                                    secondary='hacker_event_rejected')
    participants = relationship('Hacker',
                                secondary='hacker_event_participation')
    organizers = relationship("LleidaHacker",
                              secondary='lleida_hacker_event_participation')
    sponsors = relationship('Company', secondary='company_event_participation')
    groups = relationship('HackerGroup', backref='event')
    # status: int = Column(Integer, default=0)
    meals = relationship('Meal', backref='event')
