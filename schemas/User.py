# from __future__ import annotations

from pydantic import BaseModel, ValidationError, validator
from datetime import date
from typing import Optional
import re

from schemas.Userconfig import UserConfigCreate


class User(BaseModel):
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirt_size: Optional[str]
    image: Optional[str]
    is_image_url: Optional[bool]
    recive_mails: Optional[bool]
    config: UserConfigCreate

    @validator('email')
    def email_validation(cls, v):
        if (re.search(
                "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
                v) is None):
            raise ValueError('must be a valid email')
        return v

    @validator('telephone')
    def telephone_validation(cls, v):
        if re.search("^([/+][0-9]{1,2})?[0-9]{9}$", v) is None:
            raise ValueError('Value must be a valid phone number')
        return v

    @validator('password')
    def password_validation(cls, v):
        if (re.search("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$", v)
                is None):
            raise ValueError(
                'must contain at least 8 characters, at least one uppercase letter, one lowercase letter and one number'
            )
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
    recive_mails: Optional[bool]
