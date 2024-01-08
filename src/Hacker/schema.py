from src.User.schema import User, UserUpdate
from pydantic import BaseModel
from typing import Optional


class Hacker(User):
    github: str
    linkedin: str

    class Config:
        orm_mode = True


class HackerUpdate(UserUpdate):
    github: Optional[str]
    linkedin: Optional[str]
    studies: Optional[str]
    study_center: Optional[str]
    location: Optional[str]
    how_did_you_meet_us: Optional[str]
    cv: Optional[str]


class HackerGroup(BaseModel):
    name: str
    description: str
    leader_id: int
    event_id: int

    class Config:
        orm_mode = True


class HackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    leader_id: Optional[int]
