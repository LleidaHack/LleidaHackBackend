

from pydantic import BaseModel, ValidationError, validator
from typing import Optional



class UserConfigCreate(BaseModel):
    reciveNotifications: bool
    defaultLang: str
    comercialNotifications: bool
    class Config:
        orm_mode = True
    

class UserConfigGet(BaseModel):
    user_id:int
    defaultLang: str
    class Config:
        orm_mode = True



class UserConfigGetAll(UserConfigGet):
    id:int
    comercialNotifications: bool
    reciveNotifications: bool
    


class UserConfigUpdate(BaseModel):
    reciveNotifications: Optional[bool]
    defaultLang: Optional[str]
    comercialNotifications: Optional[bool]
    class Config:
        orm_mode = True
    