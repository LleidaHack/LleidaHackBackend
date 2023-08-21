from datetime import date
from pydantic import BaseModel
from typing import Optional

class Meal(BaseModel):
    name: str
    description: str
    event_id: int

class MealUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]