# from __future__ import annotations

from pydantic import BaseModel

class Event(BaseModel):
    name: str
    date: str
    location: str
    archived: bool
    description: str
    status: int
    
    # class Config:
        # orm_mode = True