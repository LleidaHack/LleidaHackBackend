from pydantic import BaseModel
from typing import Optional
from src.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class LleidaHackerCreate(UserCreate):
    role: str
    nif: str
    student: bool
    active: bool
    github: str

    # linkedin: str

    class Config:
        orm_mode = True


class LleidaHackerGet(UserGet):
    role: str
    nif: str
    student: bool
    active: bool
    github: str


class LleidaHackerGetAll(UserGetAll, LleidaHackerGet):
    pass

class LleidaHackerUpdate(UserUpdate):
    role: Optional[str]
    nif: Optional[str]
    student: Optional[bool]
    active: Optional[bool]
    github: Optional[str]
