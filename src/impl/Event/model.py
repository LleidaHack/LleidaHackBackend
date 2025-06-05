from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.HackerGroup.model import HackerGroup
    from src.impl.User.model import User
    from src.impl.LleidaHacker.model import LleidaHacker
    from src.impl.Company.model import Company
    from src.impl.Meal.model import Meal


class HackerParticipation(BaseModel):
    __tablename__ = "hacker_event_participation"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("hacker.user_id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)


class HackerRegistration(BaseModel):
    __tablename__ = "hacker_event_registration"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("hacker.user_id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)
    shirt_size: Mapped[Optional[str]] = mapped_column(String)
    food_restrictions: Mapped[Optional[str]] = mapped_column(String)
    cv: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(String, default="")
    github: Mapped[str] = mapped_column(String, default="")
    linkedin: Mapped[str] = mapped_column(String, default="")
    studies: Mapped[str] = mapped_column(String, default="")
    study_center: Mapped[str] = mapped_column(String, default="")
    location: Mapped[str] = mapped_column(String, default="")
    how_did_you_meet_us: Mapped[str] = mapped_column(String, default="")
    update_user: Mapped[bool] = mapped_column(Boolean, default=True)
    confirmed_assistance: Mapped[bool] = mapped_column(Boolean, default=False)
    confirm_assistance_token: Mapped[str] = mapped_column(String, default="")
    wants_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    # accepted: bool = mapped_column(Boolean, default=False)


class HackerAccepted(BaseModel):
    __tablename__ = "hacker_event_accepted"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("hacker.user_id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)
    # accepted: Mapped[bool] = mapped_column(Boolean, default=False)


class HackerRejected(BaseModel):
    __tablename__ = "hacker_event_rejected"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("hacker.user_id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)
    # accepted: Mapped[bool] = mapped_column(Boolean, default=False)


class LleidaHackerParticipation(BaseModel):
    __tablename__ = "lleida_hacker_event_participation"
    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("lleida_hacker.user_id"),
                                         primary_key=True,
                                         index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)


class CompanyParticipation(BaseModel):
    __tablename__ = "company_event_participation"
    company_id: Mapped[int] = mapped_column(Integer,
                                            ForeignKey("company.id"),
                                            primary_key=True,
                                            index=True)
    event_id: Mapped[int] = mapped_column(Integer,
                                          ForeignKey("event.id"),
                                          primary_key=True,
                                          index=True)


class Event(BaseModel):
    __tablename__ = 'event'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                           default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                         default=func.now())
    max_group_size: Mapped[Optional[int]] = mapped_column(Integer)
    # start_time: Mapped[Optional[Time]] = mapped_column(Time, default=func.now())
    location: Mapped[Optional[str]] = mapped_column(String)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    # status: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[int] = mapped_column(Integer, default=0)
    max_participants: Mapped[Optional[int]] = mapped_column(Integer)
    max_sponsors: Mapped[Optional[int]] = mapped_column(Integer)
    image: Mapped[Optional[str]] = mapped_column(String)
    #is_image_url: Mapped[bool] = mapped_column(Boolean, default=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)

    #TODO add registered_hackers
    # registered_hackers = relationship('Hacker',
    #                                   secondary='hacker_event_registration', uselist = True)
    registered_hackers: Mapped[List["User"]] = relationship(
        'User',
        secondary='hacker_event_registration',
        primaryjoin="Event.id==hacker_event_registration.c.event_id",
        secondaryjoin="User.id==hacker_event_registration.c.user_id",
        uselist=True)
    accepted_hackers: Mapped[List["User"]] = relationship(
        'User',
        secondary='hacker_event_accepted',
        primaryjoin="Event.id==hacker_event_accepted.c.event_id",
        secondaryjoin="User.id==hacker_event_accepted.c.user_id",
        uselist=True)
    rejected_hackers: Mapped[List["User"]] = relationship(
        'User',
        secondary='hacker_event_rejected',
        primaryjoin="Event.id==hacker_event_rejected.c.event_id",
        secondaryjoin="User.id==hacker_event_rejected.c.user_id",
        uselist=True)
    participants: Mapped[List["User"]] = relationship(
        'User',
        secondary='hacker_event_participation',
        primaryjoin="Event.id==hacker_event_participation.c.event_id",
        secondaryjoin="User.id==hacker_event_participation.c.user_id",
        uselist=True)
    organizers: Mapped[List["LleidaHacker"]] = relationship(
        "LleidaHacker",
        secondary='lleida_hacker_event_participation',
        uselist=True)
    sponsors: Mapped[List["Company"]] = relationship(
        'Company', secondary='company_event_participation', uselist=True)
    groups: Mapped[List["HackerGroup"]] = relationship('HackerGroup',
                                                       backref='event')
    # status: Mapped[int] = mapped_column(Integer, default=0)
    meals: Mapped[List["Meal"]] = relationship('Meal', backref='event')
