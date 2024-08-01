from typing import Optional

from src.utils.Base.BaseSchema import BaseSchema


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
    name: Optional[str] = None
    description: Optional[str] = None
