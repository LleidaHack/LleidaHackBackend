from utils.BaseSchema import BaseSchema
from typing import Optional


class MealCreate(BaseSchema):
    name: str
    description: str
    event_id: int


class MealGet(BaseSchema):
    name: str
    description: str
    event_id: int


class MealGetAll(MealGet):
    pass


class MealUpdate(BaseSchema):
    name: Optional[str]
    description: Optional[str]
