from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.utils.Base.BaseModel import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.impl.HackerGroup.model import HackerGroup


class HackerParticipation(BaseModel):
    __tablename__ = "hacker_event_participation"
    user_id = Column(Integer,
                     ForeignKey("hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class HackerRegistration(BaseModel):
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
    studies: str = Column(String, default="")
    study_center: str = Column(String, default="")
    location: str = Column(String, default="")
    how_did_you_meet_us: str = Column(String, default="")
    update_user: bool = Column(Boolean, default=True)
    confirmed_assistance: bool = Column(Boolean, default=False)
    confirm_assistance_token: str = Column(String, default="")
    wants_credit: bool = Column(Boolean, default=False)
    # accepted: bool = Column(Boolean, default=False)


class HackerAccepted(BaseModel):
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


class HackerRejected(BaseModel):
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


class LleidaHackerParticipation(BaseModel):
    __tablename__ = "lleida_hacker_event_participation"
    user_id = Column(Integer,
                     ForeignKey("lleida_hacker.user_id"),
                     primary_key=True,
                     index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class CompanyParticipation(BaseModel):
    __tablename__ = "company_event_participation"
    company_id = Column(Integer,
                        ForeignKey("company.id"),
                        primary_key=True,
                        index=True)
    event_id = Column(Integer,
                      ForeignKey("event.id"),
                      primary_key=True,
                      index=True)


class Event(BaseModel):
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
    # status: int = Column(Integer, default=0)
    price: int = Column(Integer, default=0)
    max_participants: int = Column(Integer)
    max_sponsors: int = Column(Integer)
    image: str = Column(String)
    #is_image_url: bool = Column(Boolean, default=False)
    is_open: bool = Column(Boolean, default=True)

    #TODO add registered_hackers
    # registered_hackers = relationship('Hacker',
    #                                   secondary='hacker_event_registration', uselist = True)
    registered_hackers = relationship(
        'User',
        secondary='hacker_event_registration',
        primaryjoin="Event.id==hacker_event_registration.c.event_id",
        secondaryjoin="User.id==hacker_event_registration.c.user_id",
        uselist=True)
    accepted_hackers = relationship(
        'User',
        secondary='hacker_event_accepted',
        primaryjoin="Event.id==hacker_event_accepted.c.event_id",
        secondaryjoin="User.id==hacker_event_accepted.c.user_id",
        uselist=True)
    rejected_hackers = relationship(
        'User',
        secondary='hacker_event_rejected',
        primaryjoin="Event.id==hacker_event_rejected.c.event_id",
        secondaryjoin="User.id==hacker_event_rejected.c.user_id",
        uselist=True)
    participants = relationship(
        'User',
        secondary='hacker_event_participation',
        primaryjoin="Event.id==hacker_event_participation.c.event_id",
        secondaryjoin="User.id==hacker_event_participation.c.user_id",
        uselist=True)
    organizers = relationship("LleidaHacker",
                              secondary='lleida_hacker_event_participation',
                              uselist=True)
    sponsors = relationship('Company',
                            secondary='company_event_participation',
                            uselist=True)
    groups: list['HackerGroup'] = relationship('HackerGroup', backref='event')
    # status: int = Column(Integer, default=0)
    meals = relationship('Meal', backref='event')
