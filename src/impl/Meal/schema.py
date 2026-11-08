from src.impl.Event.schema import EventGet
from src.utils.Base.BaseSchema import BaseSchema


class MealCreate(BaseSchema):
    name: str
    description: str
    event_id: int


class MealGet(BaseSchema):
    id: int
    name: str
    description: str
    event_id: int


class MealGetAll(MealGet):
    pass


class MealUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None


class MealCheckInResult(EventGet):
    participant: str
    food_restrictions: str | None = None
