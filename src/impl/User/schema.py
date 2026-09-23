import re
from datetime import UTC, date, datetime

from pydantic import field_serializer, field_validator

from src.impl.UserConfig.schema import UserConfigCreate, UserConfigGetAll
from src.utils.Base.BaseSchema import BaseSchema
from src.utils.security import validate_password
from src.utils.uploads import ProfileImage


class UserCreate(BaseSchema):
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str | None = None
    email: str
    telephone: str
    address: str | None = None
    shirt_size: str | None = None
    image: ProfileImage | None = None
    config: UserConfigCreate
    # is_image_url: Optional[bool] = None = None
    # recive_mails: Optional[bool] = None = None

    @field_validator("email")
    @classmethod
    def email_validation(cls, v):
        if (
            re.search(
                r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
                v,
            )
            is None
        ):
            raise ValueError("must be a valid email")
        return v

    @field_validator("telephone")
    @classmethod
    def telephone_validation(cls, v):
        if re.search("^([/+][0-9]{1,2})?[0-9]{9}$", v) is None:
            raise ValueError("must contain at least 8 digits")
        return v

    @field_validator("password")
    @classmethod
    def password_validation(cls, v):
        return validate_password(v)

    @field_validator("birthdate")
    @classmethod
    def birthdate_validation(cls, v):
        # Keep the existing timezone-naive database/local-calendar contract.
        if v > date.today():  # noqa: DTZ011
            raise ValueError("must be a valid date")
        return v

    @field_validator("shirt_size")
    @classmethod
    def shirt_size_validation(cls, v):
        if v not in ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]:
            raise ValueError("must be a valid shirt size")
        return v


class UserGet(BaseSchema):
    name: str
    nickname: str
    created_at: datetime
    type: str
    image: str | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, value):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class UserGetAll(UserGet):
    id: int
    food_restrictions: str | None = None
    birthdate: date
    email: str
    telephone: str
    address: str | None = None
    shirt_size: str | None
    is_verified: bool
    code: str
    type: str
    config: UserConfigGetAll


class UserUpdate(BaseSchema):
    name: str | None = None
    nickname: str | None = None
    password: str | None = None
    birthdate: date | None = None
    food_restrictions: str | None = None
    email: str | None = None
    telephone: str | None = None
    address: str | None = None
    shirt_size: str | None = None
    image: ProfileImage | None = None
    # is_image_url: Optional[bool] = None
    # recive_mails: Optional[bool] = None

    @field_validator("password")
    @classmethod
    def password_validation(cls, value):
        if value is None:
            raise ValueError("Password cannot be null")
        return validate_password(value)
