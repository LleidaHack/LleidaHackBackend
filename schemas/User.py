# from __future__ import annotations

from pydantic import BaseModel

class User(BaseModel):
    name: str
    nickname: str
    password: str
    birthdate: str
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirt_size: str

    class Config:
        orm_mode = True