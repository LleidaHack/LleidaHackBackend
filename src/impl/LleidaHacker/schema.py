from typing import Optional

from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate
from pydantic import ConfigDict


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
    role: Optional[str]
    nif: Optional[str]
    student: Optional[bool]
    active: Optional[bool]
    github: Optional[str]
