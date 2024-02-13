from datetime import date
from pydantic import BaseModel
from typing import Optional


class MealCreate(BaseModel):
    name: str
    description: str
    event_id: int

class MealGet(BaseModel):
    name: str
    description: str
    event_id: int

class MealGetAll(MealGet):
    pass


class MealUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
