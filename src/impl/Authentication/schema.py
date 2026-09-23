from datetime import date

from pydantic import field_validator

from src.impl.UserConfig.schema import UserConfigGetAll
from src.utils.Base.BaseSchema import BaseSchema
from src.utils.security import validate_password


class ContactMail(BaseSchema):
    name: str
    title: str
    email: str
    message: str


class ProfileGet(BaseSchema):
    id: int
    name: str | None
    nickname: str | None
    email: str | None
    type: str
    is_verified: bool
    birthdate: date | None = None
    telephone: str | None = None
    address: str | None = None
    food_restrictions: str | None = None
    shirt_size: str | None = None
    image: str | None = None
    code: str
    config: UserConfigGetAll | None = None


class VerificationResult(BaseSchema):
    success: bool


class VerificationSession(VerificationResult):
    user_id: int | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None


class PasswordResetConfirm(BaseSchema):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_validation(cls, value):
        return validate_password(value)
