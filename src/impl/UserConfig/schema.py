from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class UserConfigCreate(BaseSchema):
    recive_notifications: bool
    default_lang: str
    comercial_notifications: bool
    terms_and_conditions: bool


class UserConfigGet(BaseSchema):
    default_lang: str


class UserConfigGetAll(UserConfigGet):
    id: int
    comercial_notifications: bool
    recive_notifications: bool
    terms_and_conditions: bool


class UserConfigUpdate(BaseSchema):
    recive_notifications: bool | None = None
    default_lang: str | None = None
    comercial_notifications: bool | None = None

    @field_validator("recive_notifications", "default_lang", "comercial_notifications")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Preference values cannot be null")
        return value
