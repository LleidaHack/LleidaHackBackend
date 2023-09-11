from pydantic import BaseModel
from typing import List, Optional
from schemas.User import User, UserUpdate, UserPublic


class LleidaHacker(User):
    role: str
    nif: str
    student: bool
    active: bool
    github: str

    # linkedin: str

    class Config:
        orm_mode = True


class LleidaHackerPublic(UserPublic):
    student: bool
    active: bool
    github: str


class LleidaHackerUpdate(UserUpdate):
    role: Optional[str]
    nif: Optional[str]
    student: Optional[bool]
    active: Optional[bool]
    github: Optional[str]


class LleidaHackerGroup(BaseModel):
    name: str
    description: str
    members: List[LleidaHacker]

    # leader: int

    class Config:
        orm_mode = True


class LleidaHackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    members: Optional[List[LleidaHacker]]

    # leader: Optional[int]
