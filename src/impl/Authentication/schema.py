from pydantic import field_validator
from src.utils.security import validate_password
from datetime import date
from typing import Optional

from src.impl.UserConfig.schema import UserConfigGetAll
from src.utils.Base.BaseSchema import BaseSchema


class ContactMail(BaseSchema):
    name: str
    title: str
    email: str
    message: str


class ProfileGet(BaseSchema):
    id: int
    name: Optional[str]
    nickname: Optional[str]
    email: Optional[str]
    type: str
    is_verified: bool
    birthdate: Optional[date] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    food_restrictions: Optional[str] = None
    shirt_size: Optional[str] = None
    image: Optional[str] = None
    code: str
    config: Optional[UserConfigGetAll] = None


class VerificationResult(BaseSchema):
    success: bool


class VerificationSession(VerificationResult):
    user_id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None


class PasswordResetConfirm(BaseSchema):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_validation(cls, value):
        return validate_password(value)
