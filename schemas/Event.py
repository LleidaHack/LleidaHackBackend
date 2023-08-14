# from __future__ import annotations

from datetime import date
from pydantic import BaseModel


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
