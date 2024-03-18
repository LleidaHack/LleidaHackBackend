from typing import Optional

from pydantic import ConfigDict

from src.utils.Base.BaseSchema import BaseSchema


class HackerGroupCreate(BaseSchema):
    name: str
    description: str
    leader_id: int
    event_id: int


class HackerGroupGet(BaseSchema):
    name: str
    description: str
    leader_id: int
    event_id: int


class HackerGroupGetAll(HackerGroupGet):
    pass


class HackerGroupUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    leader_id: Optional[int] = None