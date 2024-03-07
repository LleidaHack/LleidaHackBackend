from typing import Optional

from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


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


class HackerGetAll(UserGetAll, HackerGet):
    how_did_you_meet_us: Optional[str]
    location: Optional[str]
    cv: Optional[str]
    study_center: Optional[str]


class HackerUpdate(UserUpdate):
    github: Optional[str]
    linkedin: Optional[str]
    studies: Optional[str]
    study_center: Optional[str]
    location: Optional[str]
    how_did_you_meet_us: Optional[str]
    cv: Optional[str]
