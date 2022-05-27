from __future__ import annotations
from datetime import date
from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base  = declarative_base()

# @dataclass
class Event(Base):
    __tablename__ = 'llhk_event'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    date: date = Column(DateTime, default=func.now())
    users: List[User] = relationship('User', secondary='llhk_user_event')
    location: str = Column(String)
    sponsors: List[Company] = relationship('Company', secondary='sponsor')
    archived: bool = Column(Integer, default=0)
    description: str = Column(String)
    status: int = Column(Integer, default=0)
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

    # def create(name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=0):
    #     u=User()
    #     u.id=user_id
    #     u.name=name
    #     u.nickname=nickname
    #     u.password=password
    #     u.birthdate=birthdate
    #     u.food_restrictions=food_restrictions
    #     u.email=email
    #     u.telephone=telephone
    #     u.address=address
    #     u.shirt_size=shirtSize
    #     return u


class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    role: str = Column(String)
    nif: str = Column(String)
    student: bool = Column(Integer, default=0)
    active: bool = Column(Integer, default=0)
    image: str = Column(String)
    groups: List[Group] = relationship('Group', secondary='group_user')
    github: str = Column(String)
    # def create(name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=None,role:str="",nif:str="",student:bool=False,active:bool=False,image:str="",groups:list=[],github:str=""):
    #     ll=LleidaHacker()
    #     ll.id=user_id
    #     ll.name=name
    #     ll.nickname=nickname
    #     ll.password=password
    #     ll.birthdate=birthdate
    #     ll.food_restrictions=food_restrictions
    #     ll.email=email
    #     ll.telephone=telephone
    #     ll.address=address
    #     ll.shirt_size=shirtSize
    #     ll.role=role
    #     ll.nif=nif
    #     ll.student=student
    #     ll.active=active
    #     ll.image=image
    #     ll.groups=groups
    #     ll.github=github
    #     return ll

class Company(User):
    __tablename__ = 'company'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    logo: str = Column(String)
    description: str = Column(String)
    # def create(name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, logo: str = "", description: str = ""):
    #     c=Company()
    #     c.id=user_id
    #     c.name=name
    #     c.nickname=nickname
    #     c.password=password
    #     c.birthdate=birthdate
    #     c.food_restrictions=food_restrictions
    #     c.email=email
    #     c.telephone=telephone
    #     c.address=address
    #     c.shirt_size=shirtSize
    #     c.logo=logo
    #     c.description=description
    #     return c

class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('llhk_user.id'), primary_key=True)
    banned: bool = Column(Integer, default=0)
    github: str = Column(String)
    linkdin: str = Column(String)
    # def create(name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, banned: bool = False, github: str = "", linkdin: str = ""):
    #     h=Hacker()
    #     h.id=user_id
    #     h.name=name
    #     h.nickname=nickname
    #     h.password=password
    #     h.birthdate=birthdate
    #     h.food_restrictions=food_restrictions
    #     h.email=email
    #     h.telephone=telephone
    #     h.address=address
    #     h.shirt_size=shirtSize
    #     h.banned=banned
    #     h.github=github
    #     h.linkdin=linkdin
    #     return h


class Group(Base):
    __tablename__ = 'group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    members: List[User] = relationship('User', secondary='group_user')
    leader: int = Column(Integer)
    # def create(name: str, description: str, members: list, leader: int, group_id: int = None):
    #     g=Group()
    #     g.id=group_id
    #     g.name=name
    #     g.description=description
    #     g.members=members
    #     g.leader=leader
    #     return g


class EventGroup(Base):
    __tablename__ = 'event_group'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    leader: int = Column(Integer)
    users: List[LleidaHacker] = relationship('LleidaHacker', secondary='event_group_user') 
    # def create(name:str, leader:int, users:list, id:int = None ) -> None:
    #     eg=EventGroup()
    #     eg.id=id
    #     eg.name=name
    #     eg.leader=leader
    #     eg.users=users
    #     return eg