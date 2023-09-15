# from __future__ import annotations

from pydantic import BaseModel, ValidationError, validator
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
    image: Optional[str]
    is_image_url: Optional[bool]

    @validator('email')
    def email_validation(cls, v):
        if '@' not in v:
            raise ValueError('must contain a @')
        if '.' not in v:
            raise ValueError('must contain a .')
        return v
    
    @validator('telephone')
    def telephone_validation(cls, v):
        if len(v) < 8:
            raise ValueError('must contain at least 8 digits')
        return v
    
    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('must contain at least 8 characters')
        return v

    @validator('birthdate')
    def birthdate_validation(cls, v):
        if v > date.today():
            raise ValueError('must be a valid date')
        return v
    
    @validator('shirt_size')
    def shirt_size_validation(cls, v):
        if v not in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
            raise ValueError('must be a valid shirt size')
        return v

    class Config:
        orm_mode = True
       

class UserPublic(BaseModel):
    id: int
    name: str
    nickname: str
    birthdate: date
    image: Optional[str]
    is_image_url: Optional[bool]


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
    image: Optional[str]
    is_image_url: Optional[bool]
