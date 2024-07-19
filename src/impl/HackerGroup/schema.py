from typing import Optional, List

from pydantic import ConfigDict

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
    members: List[object]


class HackerGroupGetAll(HackerGroupGet):
    code: str
    pass


class HackerGroupUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    leader_id: Optional[int] = None
