from __future__ import annotations

from pydantic import BaseModel
from typing import List

class Event(BaseModel):
    name: str
    date: str
    location: str
    archived: bool
    description: str
    status: int
    
    # class Config:
        # orm_mode = True

class User(BaseModel):
    name: str
    nickname: str
    password: str
    birthdate: str
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirt_size: str

    # class Config:
        # orm_mode = True

class LleidaHacker(User):
    role: str
    nif: str
    student: bool 
    active: bool 
    image: str 
    github: str 

    # class Config:
        # orm_mode = True

class Company(BaseModel):
    name: str
    description: str
    website: str
    logo: str
    address: str
    telephone: str
    users: List[User]
    # events: List[Event]

    # class Config:
        # orm_mode = True

class CompanyUser(BaseModel):
    pass

    # class Config:
        # orm_mode = True

class Hacker(User):
    banned: bool
    github: str
    linkdin: str

    # class Config:
        # orm_mode = True

class LleidaHackerGroup(BaseModel):
    name: str
    description: str
    members: List[LleidaHacker]
    leader: int

    # class Config:
        # orm_mode = True

class HackerGroup(BaseModel):
    name: str
    description: str
    members: List[Hacker]
    leader: int

    # class Config:
        # orm_mode = True