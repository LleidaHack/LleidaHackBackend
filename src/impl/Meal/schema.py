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
