# from __future__ import annotations

from pydantic import BaseModel
from datetime import date


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
