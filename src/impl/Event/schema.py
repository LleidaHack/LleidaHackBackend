# from __future__ import annotations
from typing import Optional
from datetime import date
from pydantic import validator

from utils.BaseSchema import BaseSchema


class EventCreate(BaseSchema):
    name: str
    description: str
    start_date: date
    end_date: date
    location: str
    archived: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    status: int
    image: Optional[str]
    is_image_url: Optional[bool]

    # start_time: Time = Column(Time, default=func.now())

    @validator('max_participants')
    def max_participants_validation(cls, v):
        if v < 0:
            raise ValueError('must be a valid number')
        return v

    @validator('max_group_size')
    def max_group_size_validation(cls, v):
        if v <= 0:
            raise ValueError('must be a valid number')
        return v

    @validator('max_sponsors')
    def max_sponsors_validation(cls, v):
        if v < 0:
            raise ValueError('must be a valid number')
        return v


class EventGet(BaseSchema):
    name: str
    description: str
    start_date: date
    end_date: date
    location: str
    archived: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    status: int
    image: Optional[str]
    is_image_url: Optional[bool]


class EventGetAll(EventGet):
    pass


class EventUpdate(BaseSchema):
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
class HackerEventRegistration(BaseSchema):
    shirt_size: str
    food_restrictions: str
    cv: Optional[str]
    description: Optional[str]
    github: Optional[str]
    linkedin: Optional[str]
    dailyhack_url: Optional[str]
    studies: str
    study_center: str
    location: str
    how_did_you_meet_us: str
    update_user: bool

    @validator('shirt_size')
    def shirt_size_validation(cls, v):
        if v not in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
            raise ValueError('must be a valid shirt size')
        return v


class HackerEventRegistrationUpdate(BaseSchema):
    shirt_size: Optional[str]
    food_restrictions: Optional[str]
    cv: Optional[str]
    description: Optional[str]
    dailyhack_url: Optional[str]
    github: Optional[str]
    linkedin: Optional[str]
    studies: Optional[str]
    study_center: Optional[str]
    location: Optional[str]
    how_did_you_meet_us: Optional[str]
