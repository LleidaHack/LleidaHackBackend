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

    # start_time: Time = Column(Time, default=func.now())