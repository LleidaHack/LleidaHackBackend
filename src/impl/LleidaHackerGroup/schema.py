from typing import Optional

from src.utils.Base.BaseSchema import BaseSchema


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
    name: Optional[str] = None
    description: Optional[str] = None
    # leader: Optional[int]
