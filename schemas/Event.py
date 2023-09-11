# from __future__ import annotations

from datetime import date
from pydantic import BaseModel
from typing import Optional


class Event(BaseModel):
    name: str
    description: str
    start_date: date
    end_date: date
    location: str
    archived: bool
    price: int
    max_participants: int
    max_sponsors: int
    status: int
    image: Optional[str]
    is_image_url: Optional[bool]

    # start_time: Time = Column(Time, default=func.now())

    class Config:
        orm_mode = True


class EventUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    location: Optional[str]
    archived: Optional[bool]
    price: Optional[int]
    max_participants: Optional[int]
    max_sponsors: Optional[int]
    status: Optional[int]
    image: Optional[str]
    is_image_url: Optional[bool]
    is_open: Optional[bool]
    max_group_size: Optional[int]


    # start_time: Time = Column(Time, default=func.now())
class HackerEventRegistration(BaseModel):
    shirt_size: str
    food_restrictions: str
    cv: Optional[str]
    description: Optional[str]
    github: Optional[str]
    linkedin: Optional[str]
    dailyhack_url: Optional[str]
    update_user: bool


class HackerEventRegistrationUpdate(BaseModel):
    shirt_size: Optional[str]
    food_restrictions: Optional[str]
    cv: Optional[str]
    description: Optional[str]
    dailyhack_url: Optional[str]
