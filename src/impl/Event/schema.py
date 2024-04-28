# from __future__ import annotations
from datetime import date
from typing import Optional

from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


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
    image: Optional[str] = None
    is_image_url: Optional[bool] = None

    # start_time: Time = Column(Time, default=func.now())

    @field_validator('max_participants')
    @classmethod
    def max_participants_validation(cls, v):
        if v < 0:
            raise ValueError('must be a valid number')
        return v

    @field_validator('max_group_size')
    @classmethod
    def max_group_size_validation(cls, v):
        if v <= 0:
            raise ValueError('must be a valid number')
        return v

    @field_validator('max_sponsors')
    @classmethod
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
    image: Optional[str] = None
    is_image_url: Optional[bool] = None


class EventGetAll(EventGet):
    pass


class EventUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    archived: Optional[bool] = None
    price: Optional[int] = None
    max_participants: Optional[int] = None
    max_sponsors: Optional[int] = None
    image: Optional[str] = None
    is_image_url: Optional[bool] = None
    is_open: Optional[bool] = None
    max_group_size: Optional[int] = None


    # start_time: Time = Column(Time, default=func.now())
class HackerEventRegistration(BaseSchema):
    shirt_size: str
    food_restrictions: str
    cv: Optional[str] = None
    description: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: str
    study_center: str
    location: str
    how_did_you_meet_us: str
    update_user: bool

    @field_validator('shirt_size')
    @classmethod
    def shirt_size_validation(cls, v):
        if v not in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
            raise ValueError('must be a valid shirt size')
        return v


class HackerEventRegistrationUpdate(BaseSchema):
    shirt_size: Optional[str] = None
    food_restrictions: Optional[str] = None
    cv: Optional[str] = None
    description: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: Optional[str] = None
    study_center: Optional[str] = None
    location: Optional[str] = None
    how_did_you_meet_us: Optional[str] = None
