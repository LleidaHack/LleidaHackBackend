from schemas.User import User, UserUpdate
from pydantic import BaseModel
from typing import List, Optional


class Hacker(User):
    github: str
    linkedin: str

    class Config:
        orm_mode = True

class HackerUpdate(UserUpdate):
    github: Optional[str]
    linkedin: Optional[str]

class HackerGroup(BaseModel):
    name: str
    description: str
    members: List[Hacker]
    leader: int

    class Config:
        orm_mode = True

class HackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    members: Optional[List[Hacker]]
    leader: Optional[int]