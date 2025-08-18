from datetime import datetime
from typing import Optional

from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class ActivityGet(BaseSchema):
    id: int
    edition: int
    title: str
    description: Optional[str]
    sponsor: Optional[str]
    location: Optional[str]
    day_time: datetime


class ActivityCreate(BaseSchema):
    edition: int
    title: str
    description: Optional[str] = None
    sponsor: Optional[str] = None
    location: Optional[str] = None
    day_time: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_validation(cls, v):
        if len(v) < 5:
            raise ValueError("title must be at least 5 characters long")
        return v


class ActivityUpdate(BaseSchema):
    edition: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    sponsor: Optional[str] = None
    location: Optional[str] = None
    day_time: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_validation(cls, v):
        if v is not None and len(v) < 5:
            raise ValueError("title must be at least 5 characters long")
        return v
