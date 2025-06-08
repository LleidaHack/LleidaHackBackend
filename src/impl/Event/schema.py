# from __future__ import annotations
from datetime import datetime

from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class EventCreate(BaseSchema):
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    archived: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    image: str | None = None
    # is_image_url: Optional[bool] = None

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
    id: int
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    archived: bool
    is_open: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    image: str | None = None
    # is_image_url: Optional[bool] = None


class EventGetAll(EventGet):
    pass


class EventUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str | None = None
    archived: bool | None = None
    price: int | None = None
    max_participants: int | None = None
    max_sponsors: int | None = None
    image: str | None = None
    # is_image_url: Optional[bool] = None
    is_open: bool | None = None
    max_group_size: int | None = None

    # start_time: Time = Column(Time, default=func.now())


class HackerEventRegistration(BaseSchema):
    shirt_size: str
    food_restrictions: str
    cv: str | None = None
    description: str | None = None
    github: str | None = None
    linkedin: str | None = None
    studies: str
    study_center: str
    location: str
    how_did_you_meet_us: str
    wants_credit: bool
    update_user: bool

    @field_validator('shirt_size')
    @classmethod
    def shirt_size_validation(cls, v):
        if v not in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
            raise ValueError('must be a valid shirt size')
        return v


class HackerEventRegistrationUpdate(BaseSchema):
    shirt_size: str | None = None
    food_restrictions: str | None = None
    cv: str | None = None
    description: str | None = None
    github: str | None = None
    linkedin: str | None = None
    studies: str | None = None
    study_center: str | None = None
    location: str | None = None
    how_did_you_meet_us: str | None = None
    wants_credit: bool | None = False
