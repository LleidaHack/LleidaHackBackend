from __future__ import annotations

from pydantic import BaseModel
from typing import List

class Event(BaseModel):
    id: int
    name: str
    date: str
    users: List[User]
    location: str
    sponsors: List[Company]
    archived: bool
    description: str
    status: int

class User(BaseModel):
    id: int
    name: str
    nickname: str
    password: str
    birthdate: str
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirtSize: str

    class Config:
        orm_mode = True

class LleidaHacker(User):
    user_id: int
    role: str
    nif: str
    student: bool 
    active: bool 
    image: str 
    groups: List[Group] 
    github: str 

    class Config:
        orm_mode = True

class Company(User):
    logo: str
    description: str

    class Config:
        orm_mode = True

class Hacker(User):
    banned: bool
    github: str
    linkdin: str

    class Config:
        orm_mode = True

class Group(BaseModel):
    id: int
    name: str
    description: str
    members: List[User]
    leader: int

    class Config:
        orm_mode = True

class EventGroup(BaseModel):
    id: int
    name: str
    leader: int
    users: List[LleidaHacker]

    class Config:
        orm_mode = True