from typing import Optional

from pydantic import ConfigDict

from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class LleidaHackerCreate(UserCreate):
    role: str
    nif: str
    student: bool
    active: bool
    github: str


class LleidaHackerGet(UserGet):
    role: str
    nif: str
    student: bool
    active: bool
    github: str


class LleidaHackerGetAll(UserGetAll, LleidaHackerGet):
    pass


class LleidaHackerUpdate(UserUpdate):
    role: Optional[str] = None
    nif: Optional[str] = None
    student: Optional[bool] = None
    active: Optional[bool] = None
    github: Optional[str] = None
