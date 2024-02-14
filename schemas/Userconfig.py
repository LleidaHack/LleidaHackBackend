

from pydantic import BaseModel, ValidationError, validator
from typing import Optional



class UserConfigCreate(BaseModel):
    reciveNotifications: bool
    defaultLang: str
    comercialNotifications: bool
    

class UserConfigGet(BaseModel):
    reciveNotifications: bool
    defaultLang: str
    comercialNotifications: bool



class UserConfigGetAll(UserConfigGet):
    pass



class UserConfigUpdate(BaseModel):
    reciveNotifications: Optional[bool]
    defaultLang: Optional[str]
    comercialNotifications: Optional[bool]
    