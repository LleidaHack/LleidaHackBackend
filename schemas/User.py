# from __future__ import annotations

from pydantic import BaseModel
from datetime import date
from typing import Optional


class User(BaseModel):
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirt_size: str
    image_id: str

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    name: Optional[str]
    nickname: Optional[str]
    password: Optional[str]
    birthdate: Optional[date]
    food_restrictions: Optional[str]
    email: Optional[str]
    telephone: Optional[str]
    address: Optional[str]
    shirt_size: Optional[str]
    image_id: Optional[str]
