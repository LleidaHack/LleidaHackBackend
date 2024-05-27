from typing import Optional

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
    recive_notifications: Optional[bool]
    default_lang: Optional[str]
    comercial_notifications: Optional[bool]
