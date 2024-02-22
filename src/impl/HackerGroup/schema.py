from src.utils.Base.BaseSchema import BaseSchema
from typing import Optional


class HackerGroupCreate(BaseSchema):
    name: str
    description: str
    leader_id: int
    event_id: int

    class Config:
        orm_mode = True


class HackerGroupGet(BaseSchema):
    name: str
    description: str
    leader_id: int
    event_id: int


class HackerGroupGetAll(HackerGroupGet):
    pass


class HackerGroupUpdate(BaseSchema):
    name: Optional[str]
    description: Optional[str]
    leader_id: Optional[int]
