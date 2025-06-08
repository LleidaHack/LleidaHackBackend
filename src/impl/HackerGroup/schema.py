from src.impl.Hacker.schema import HackerGet
from src.utils.Base.BaseSchema import BaseSchema


class HackerGroupCreate(BaseSchema):
    name: str
    description: str
    leader_id: int
    event_id: int


class HackerGroupGet(BaseSchema):
    id: int
    name: str
    description: str
    leader_id: int
    event_id: int
    members: list[HackerGet]


class HackerGroupGetAll(HackerGroupGet):
    code: str
    pass


class HackerGroupUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    leader_id: int | None = None
