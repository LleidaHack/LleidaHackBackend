from __future__ import annotations
from datetime import date
from typing import List
from pydantic import BaseModel
from dataclasses import dataclass

# @dataclass
class Event(BaseModel):
    id: int = None
    name: str = None
    date: date = None
    users: List[User] = []
    location: str = None
    sponsors: List[Company] = []
    archived: bool = False
    description: str = None
    status: int = 0
    def __init__(self,event_id:int,name:str,date:date,location:str,description:str,status:int,sponsors:List[Company]=[]):
        e=Event()
        e.id=event_id
        e.name=name
        e.date=date
        e.location=location
        e.description=description
        e.status=status
        e.sponsors=sponsors
        e.users=[]
        e.archived=False
        return e

# @dataclass
class User(BaseModel):
    id: int = None
    name: str=None
    nickname: str=None
    password: str=None
    birthdate: date=None
    food_restrictions: str=None
    email: str=None
    telephone: str=None
    address: str=None
    shirt_size: str=None

    def create(name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=0):
        u=User()
        u.id=user_id
        u.name=name
        u.nickname=nickname
        u.password=password
        u.birthdate=birthdate
        u.food_restrictions=food_restrictions
        u.email=email
        u.telephone=telephone
        u.address=address
        u.shirt_size=shirtSize
        return u


class LleidaHacker(User):
    role: str = None
    nif: str = None
    student: bool = True
    active: bool = False
    image: str = None
    groups: List[str] = []
    github: str = None
    def create(name:str,nickname:str,password:str,birthdate:date,food_restrictions:str,email:str,telephone:str,address:str,shirtSize:str,user_id:int=None,role:str="",nif:str="",student:bool=False,active:bool=False,image:str="",groups:list=[],github:str=""):
        ll=LleidaHacker()
        ll.id=user_id
        ll.name=name
        ll.nickname=nickname
        ll.password=password
        ll.birthdate=birthdate
        ll.food_restrictions=food_restrictions
        ll.email=email
        ll.telephone=telephone
        ll.address=address
        ll.shirt_size=shirtSize
        ll.role=role
        ll.nif=nif
        ll.student=student
        ll.active=active
        ll.image=image
        ll.groups=groups
        ll.github=github
        return ll

# @dataclass
class Company(User):
    logo: str = None
    description: str = None
    def create(name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, logo: str = "", description: str = ""):
        c=Company()
        c.id=user_id
        c.name=name
        c.nickname=nickname
        c.password=password
        c.birthdate=birthdate
        c.food_restrictions=food_restrictions
        c.email=email
        c.telephone=telephone
        c.address=address
        c.shirt_size=shirtSize
        c.logo=logo
        c.description=description
        return c

# @dataclass
class Hacker(User):
    banned: bool = False
    github: str = None
    linkdin: str = None
    def create(name: str, nickname: str, password: str, birthdate: date, food_restrictions: str, email: str, telephone: str, address: str, shirtSize: str, user_id: int = None, banned: bool = False, github: str = "", linkdin: str = ""):
        h=Hacker()
        h.id=user_id
        h.name=name
        h.nickname=nickname
        h.password=password
        h.birthdate=birthdate
        h.food_restrictions=food_restrictions
        h.email=email
        h.telephone=telephone
        h.address=address
        h.shirt_size=shirtSize
        h.banned=banned
        h.github=github
        h.linkdin=linkdin
        return h


class Group(BaseModel):
    id: int = None
    name: str = None
    description: str = None
    members: List[User] = []
    leader: int = None
    def create(name: str, description: str, members: list, leader: int, group_id: int = None):
        g=Group()
        g.id=group_id
        g.name=name
        g.description=description
        g.members=members
        g.leader=leader
        return g


class EventGroup(BaseModel):
    id: int = None
    name: str = None
    leader: int = None
    users: List[User] = []
    def create(name:str, leader:int, users:list, id:int = None ) -> None:
        eg=EventGroup()
        eg.id=id
        eg.name=name
        eg.leader=leader
        eg.users=users
        return eg