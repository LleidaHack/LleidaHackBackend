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

class Company(User):
    logo: str
    description: str

    # class Config:
        # orm_mode = True

class Hacker(User):
    banned: bool
    github: str
    linkdin: str

    # class Config:
        # orm_mode = True

class Group(BaseModel):
    name: str
    description: str
    members: List[User]
    leader: int

    # class Config:
        # orm_mode = True

class EventGroup(BaseModel):
    name: str
    leader: int

    # class Config:
        # orm_mode = True