from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, List


from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.impl.Hacker.model import Hacker
    from src.impl.Company.model import Company
    from src.impl.HackerGroup.model import HackerGroup
    from src.impl.LleidaHacker.model import LleidaHacker
    from src.impl.Meal.model import Meal
    from src.impl.User.model import User


class HackerParticipation(SQLModel, table=True):
    __tablename__ = "hacker_event_participation"
    user_id: int = Field(foreign_key="hacker.user_id",
                     primary_key=True,
                     index=True)
    event_id: int = Field(foreign_key="event.id",
                      primary_key=True,
                      index=True)


class HackerRegistration(SQLModel, table=True):
    __tablename__ = "hacker_event_registration"
    user_id: int = Field(foreign_key="hacker.user_id",
                     primary_key=True,
                     index=True)
    event_id: int = Field(foreign_key="event.id",
                      primary_key=True,
                      index=True)
    shirt_size: str
    food_restrictions: str
    cv: str = Field(default="")
    description: str = Field(default="")
    github: str = Field(default="")
    linkedin: str = Field(default="")
    studies: str = Field(default="")
    study_center: str = Field(default="")
    location: str = Field(default="")
    how_did_you_meet_us: str = Field(default="")
    update_user: bool = Field(default=True)
    confirmed_assistance: bool = Field(default=False)
    confirm_assistance_token: str = Field(default="")
    # accepted: bool = Column(Boolean, default=False)


class HackerAccepted(SQLModel, table=True):
    __tablename__ = "hacker_event_accepted"
    user_id: int = Field(foreign_key="hacker.user_id",
                     primary_key=True,
                     index=True)
    event_id: int = Field(foreign_key="event.id",
                      primary_key=True,
                      index=True)
    # accepted: bool = Column(Boolean, default=False)


class HackerRejected(SQLModel, table=True):
    __tablename__ = "hacker_event_rejected"
    user_id: int = Field( foreign_key="hacker.user_id",
                     primary_key=True,
                     index=True)
    event_id: int = Field(foreign_key="event.id",
                      primary_key=True,
                      index=True)
    # accepted: bool = Column(Boolean, default=False)


class LleidaHackerParticipation(SQLModel, table=True):
    __tablename__ = "lleida_hacker_event_participation"
    user_id: int = Field(foreign_key="lleida_hacker.user_id",
                     primary_key=True,
                     index=True)
    event_id: int = Field(foreign_key="event.id",
                      primary_key=True,
                      index=True)


class CompanyParticipation(SQLModel, table=True):
    __tablename__ = "company_event_participation"
    company_id: int = Field(
                        foreign_key ="company.id",
                        primary_key=True,
                        index=True)
    event_id: int = Field(
                      foreign_key = "event.id",
                      primary_key=True,
                      index=True)

from sqlalchemy.orm import RelationshipProperty
class Event(SQLModel, table = True):
    id: int = Field(primary_key=True, index=True)
    name: str
    description: str
    start_date: date = Field(default=func.now())
    end_date: date = Field(default=func.now())
    max_group_size: int
    location: str
    archived: bool = Field(default=False)
    price: int = Field(default=0)
    max_participants: int
    max_sponsors: int
    image: str
    is_open: bool = Field(default=True)

    #TODO add registered_hackers
    # registered_hackers = relationship('Hacker',
    #                                   secondary='hacker_event_registration', uselist = True)
    registered_hackers: List['Hacker'] = Relationship(back_populates='events', link_model=HackerRegistration)
        # sa_relationship=RelationshipProperty('hacker',
        #                                      primaryjoin="Event.id==hacker_event_registration.c.event_id",
        #                                      secondaryjoin="User.id==hacker_event_registration.c.user_id"))
    # accepted_hackers: list['User'] = Relationship(
    #     link_model=HackerAccepted,
    #     sa_relationship=RelationshipProperty('my_user',
    #                                          primaryjoin = "Event.id==hacker_event_accepted.c.event_id",
    #                                          secondaryjoin="User.id==hacker_event_accepted.c.user_id"))
    # rejected_hackers: list['User'] = Relationship(
    #     link_model=HackerRejected,
    #     sa_relationship=RelationshipProperty('my_user',
    #                                          primaryjoin="Event.id==hacker_event_rejected.c.event_id",
    #                                          secondaryjoin="User.id==hacker_event_rejected.c.user_id"))
    # participants: list['User'] = Relationship(
    #     link_model=HackerParticipation,
    #     sa_relationship=RelationshipProperty('my_user',
    #                                          primaryjoin="Event.id==hacker_event_participation.c.event_id",
    #                                          secondaryjoin="User.id==hacker_event_participation.c.user_id"))
    organizers: list['LleidaHacker'] = Relationship(link_model=LleidaHackerParticipation)
    sponsors: list['Company'] = Relationship(link_model=CompanyParticipation)
    groups: list['HackerGroup'] = Relationship(back_populates='event')
    # status: int = Column(Integer, default=0)
    meals: list['Meal'] = Relationship(back_populates='event')
