from src.User.schema import UserGet, UserGetAll, UserUpdate
from pydantic import BaseModel
from typing import Optional

class HackerGroupCreate(BaseModel):
    name: str
    description: str
    leader_id: int
    event_id: int

    class Config:
        orm_mode = True

class HackerGroupGet(BaseModel):
    name: str
    description: str
    leader_id: int
    event_id: int

class HackerGroupGetAll(HackerGroupGet):
    pass

class HackerGroupUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    leader_id: Optional[int]