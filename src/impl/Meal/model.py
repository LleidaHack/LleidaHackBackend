from typing import List

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel

from src.impl.Hacker.model import Hacker



class HackerMeal(SQLModel, table=True):
    __tablename__ = "hacker_meal"
    user_id: int = Field(foreign_key="hacker.user_id",
                     primary_key=True,
                     index=True)
    meal_id: int = Field(foreign_key="meal.id",
                     primary_key=True,
                     index=True)


class Meal(SQLModel, table=True):
    __tablename__ = 'meal'
    id: int = Field(primary_key=True, index=True)
    event_id: int = Field(foreign_key='event.id', index=True)
    name: str
    description: str
    users: list['Hacker'] = Relationship(link_model=HackerMeal)
