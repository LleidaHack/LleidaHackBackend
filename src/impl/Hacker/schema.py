from typing import Optional

from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class HackerCreate(UserCreate):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    study_center: Optional[str] = None
    location: Optional[str] = None
    how_did_you_meet_us: Optional[str] = None
    cv: Optional[str] = None


class HackerGet(UserGet):
    github: str
    linkedin: str


class HackerGetAll(UserGetAll, HackerGet):
    how_did_you_meet_us: Optional[str]
    location: Optional[str]
    cv: Optional[str]
    study_center: Optional[str]
    banned: int


class HackerUpdate(UserUpdate):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: Optional[str] = None
    study_center: Optional[str] = None
    location: Optional[str] = None
    how_did_you_meet_us: Optional[str] = None
    cv: Optional[str] = None
