import re
from datetime import date
from typing import Optional

from pydantic import field_validator

from src.impl.UserConfig.schema import UserConfigCreate, UserConfigGetAll
from src.utils.Base.BaseSchema import BaseSchema


class UserCreate(BaseSchema):
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirt_size: Optional[str] = None
    image: Optional[str] = None
    config: UserConfigCreate
    # is_image_url: Optional[bool] = None
    # recive_mails: Optional[bool] = None

    @field_validator('email')
    @classmethod
    def email_validation(cls, v):
        if (re.search(
                "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
                v) is None):
            raise ValueError('must be a valid email')
        return v

    @field_validator('telephone')
    @classmethod
    def telephone_validation(cls, v):
        if re.search("^([/+][0-9]{1,2})?[0-9]{9}$", v) is None:
            raise ValueError('must contain at least 8 digits')
        return v

    @field_validator('password')
    @classmethod
    def password_validation(cls, v):
        if (re.search("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$", v)
                is None):
            raise ValueError(
                'must contain at least 8 characters, at least one uppercase letter, one lowercase letter and one number'
            )
        return v

    @field_validator('birthdate')
    @classmethod
    def birthdate_validation(cls, v):
        if v > date.today():
            raise ValueError('must be a valid date')
        return v

    @field_validator('shirt_size')
    @classmethod
    def shirt_size_validation(cls, v):
        if v not in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
            raise ValueError('must be a valid shirt size')
        return v


class UserGet(BaseSchema):
    name: str
    nickname: str
    birthdate: date
    email: str
    image: Optional[str] = None


class UserGetAll(UserGet):
    id: int
    food_restrictions: str
    telephone: str
    address: str
    shirt_size: Optional[str]
    is_verified: bool
    code: str
    type: str
    config: UserConfigGetAll 


class UserUpdate(BaseSchema):
    name: Optional[str] = None
    nickname: Optional[str] = None
    password: Optional[str] = None
    birthdate: Optional[date] = None
    food_restrictions: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    shirt_size: Optional[str] = None
    image: Optional[str] = None
    # is_image_url: Optional[bool] = None
    # recive_mails: Optional[bool] = None
