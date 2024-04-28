from typing import Optional

from src.utils.Base.BaseSchema import BaseSchema


class UserConfigCreate(BaseSchema):
    reciveNotifications: bool
    defaultLang: str
    comercialNotifications: bool
    terms_and_conditions: bool


class UserConfigGet(BaseSchema):
    defaultLang: str


class UserConfigGetAll(UserConfigGet):
    id: int
    comercialNotifications: bool
    reciveNotifications: bool
    terms_and_conditions: bool


class UserConfigUpdate(BaseSchema):
    reciveNotifications: Optional[bool]
    defaultLang: Optional[str]
    comercialNotifications: Optional[bool]
