from src.impl.User.schema import UserGet
from src.utils.Base.BaseSchema import BaseSchema


class LleidaHackerGroupCreate(BaseSchema):
    name: str
    description: str


class LleidaHackerGroupGet(BaseSchema):
    name: str
    description: str
    leader: list[UserGet]


class LleidaHackerGroupGetAll(LleidaHackerGroupGet):
    pass


class LleidaHackerGroupUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
