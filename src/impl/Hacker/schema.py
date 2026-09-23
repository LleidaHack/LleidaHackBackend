from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate
from src.utils.uploads import Curriculum


class HackerCreate(UserCreate):
    github: str | None = None
    linkedin: str | None = None
    study_center: str | None = None
    location: str | None = None
    how_did_you_meet_us: str | None = None
    cv: Curriculum | None = None


class HackerGet(UserGet):
    # Exposed so group members can be identified (e.g. leader kicking a member).
    id: int
    github: str
    linkedin: str


class HackerGetAll(UserGetAll, HackerGet):
    how_did_you_meet_us: str | None
    location: str | None
    cv: str | None
    study_center: str | None
    studies: str | None
    banned: int


class HackerUpdate(UserUpdate):
    github: str | None = None
    linkedin: str | None = None
    studies: str | None = None
    study_center: str | None = None
    location: str | None = None
    how_did_you_meet_us: str | None = None
    cv: Curriculum | None = None
