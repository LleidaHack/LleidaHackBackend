from src.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate
from pydantic import BaseModel
from typing import Optional

class HackerCreate(UserCreate):
    github: str
    linkedin: str
    study_center: Optional[str]
    location: Optional[str]
    how_did_you_meet_us: Optional[str]
    cv: Optional[str]

class HackerGet(UserGet):
    github: str
    linkedin: str
    study_center: str
    location: str
    how_did_you_meet_us: str
    cv: str

class HackerGetAll(UserGetAll, HackerGet):
    pass

class HackerUpdate(UserUpdate):
    github: Optional[str]
    linkedin: Optional[str]
    studies: Optional[str]
    study_center: Optional[str]
    location: Optional[str]
    how_did_you_meet_us: Optional[str]
    cv: Optional[str]
