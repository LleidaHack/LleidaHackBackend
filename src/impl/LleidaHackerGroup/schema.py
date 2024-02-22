from src.utils.Base.BaseSchema import BaseSchema
from typing import Optional


class LleidaHackerGroupCreate(BaseSchema):
    name: str
    description: str
    # leader: int


class LleidaHackerGroupGet(BaseSchema):
    name: str
    description: str


class LleidaHackerGroupGetAll(BaseSchema):
    pass


class LleidaHackerGroupUpdate(BaseSchema):
    name: Optional[str]
    description: Optional[str]
    # leader: Optional[int]
