from __future__ import annotations
from datetime import date
from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# @dataclass
# class Event(Base):
#     __tablename__ = 'llhk_event'
#     id: int = Column(Integer, primary_key=True, index=True)
#     name: str = Column(String)
#     date: date = Column(DateTime, default=func.now())
#     users: List[User] = relationship('User', secondary='llhk_user_event')
#     location: str = Column(String)
#     sponsors: List[Company] = relationship('Company', secondary='sponsor')
#     archived: bool = Column(Integer, default=0)
#     description: str = Column(String)
#     status: int = Column(Integer, default=0)
    # def create(event_id:int,name:str,date:date,location:str,description:str,status:int,sponsors:List[Company]=[]):
    #     e=Event()
    #     e.id=event_id
    #     e.name=name
    #     e.date=date
    #     e.location=location
    #     e.description=description
    #     e.status=status
    #     e.sponsors=sponsors
    #     e.users=[]
    #     e.archived=False
    #     return e

# @dataclass
class User(Base):
    __tablename__ = 'llhk_user'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    nickname: str = Column(String)
    password: str = Column(String)
    birthdate: date = Column(DateTime)
    food_restrictions: str = Column(String)
    email: str = Column(String)
    telephone: str = Column(String)
    address: str = Column(String)
    shirt_size: str = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "llhk_user",
        "polymorphic_on": type,
    }


class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    role: str = Column(String)
    nif: str = Column(String)
    student: bool = Column(Integer, default=0)
    active: bool = Column(Integer, default=0)
    image: str = Column(String)
    # groups: List[Group] = relationship('Group', secondary='group_user')
    github: str = Column(String)
    
    __mapper_args__ = {
        "polymorphic_identity": "lleida_hacker",
    }

class Company(User):
    __tablename__ = 'company'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    logo: str = Column(String)
    description: str = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "company",
    }

class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    banned: bool = Column(Integer, default=0)
    github: str = Column(String)
    linkdin: str = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "hacker",
    }

# class Group(Base):
#     __tablename__ = 'group'
#     id: int = Column(Integer, primary_key=True, index=True)
#     name: str = Column(String)
#     description: str = Column(String)
#     members: List[User] = relationship('User', secondary='group_user')
#     leader: int = Column(Integer)


# class EventGroup(Base):
#     __tablename__ = 'event_group'
#     id: int = Column(Integer, primary_key=True, index=True)
#     name: str = Column(String)
#     leader: int = Column(Integer)
#     users: List[LleidaHacker] = relationship('LleidaHacker', secondary='event_group_user') 
