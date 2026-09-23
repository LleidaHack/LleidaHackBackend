from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class LleidaHackerCreate(UserCreate):
    role: str
    nif: str
    student: bool
    active: bool
    github: str
    linkedin: str


class LleidaHackerGet(UserGet):
    user_id: int
    role: str
    student: bool
    active: bool
    github: str
    linkedin: str


class LleidaHackerGetAll(UserGetAll, LleidaHackerGet):
    nif: str


class LleidaHackerUpdate(UserUpdate):
    role: str | None = None
    nif: str | None = None
    student: bool | None = None
    active: bool | None = None
    github: str | None = None
    linkedin: str | None = None
