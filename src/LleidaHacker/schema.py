from pydantic import BaseModel
from typing import Optional
from src.User.schema import User, UserUpdate


class LleidaHacker(User):
    role: str
    nif: str
    student: bool
    active: bool
    github: str

    # linkedin: str

    class Config:
        orm_mode = True


class LleidaHackerUpdate(UserUpdate):
    role: Optional[str]
    nif: Optional[str]
    student: Optional[bool]
    active: Optional[bool]
    github: Optional[str]


class LleidaHackerGroup(BaseModel):
    name: str
    description: str

    # leader: int

    class Config:
        orm_mode = True


class LleidaHackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]

    # leader: Optional[int]
