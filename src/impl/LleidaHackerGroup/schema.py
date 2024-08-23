from typing import List, Optional

from src.impl.User.schema import UserGet
from src.utils.Base.BaseSchema import BaseSchema


class LleidaHackerGroupCreate(BaseSchema):
    name: str
    description: str

class LleidaHackerGroupGet(BaseSchema):
    name: str
    description: str
    leader: List[UserGet]

class LleidaHackerGroupGetAll(LleidaHackerGroupGet):
    pass


class LleidaHackerGroupUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
