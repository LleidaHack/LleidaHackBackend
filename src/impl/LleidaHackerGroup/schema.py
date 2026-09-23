from pydantic import Field

from src.impl.LleidaHacker.schema import LleidaHackerGet
from src.impl.User.schema import UserGet
from src.utils.Base.BaseSchema import BaseSchema


class LleidaHackerGroupCreate(BaseSchema):
    name: str
    description: str


class LleidaHackerGroupGet(BaseSchema):
    id: int
    name: str
    description: str
    leader: list[UserGet] = Field(validation_alias="leaders")
    members: list[LleidaHackerGet]


class LleidaHackerGroupGetAll(LleidaHackerGroupGet):
    pass


class LleidaHackerGroupUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None


class LleidaHackerGroupSorted(BaseSchema):
    name: str
    img: str | None
    leaders: list[LleidaHackerGet]
    members: list[LleidaHackerGet]


class LleidaHackerGroupsSorted(BaseSchema):
    llhk_groups: list[LleidaHackerGroupSorted]
