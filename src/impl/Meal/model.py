from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.Hacker.model import Hacker


class HackerMeal(BaseModel):
    __tablename__ = 'hacker_meal'
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('hacker.user_id'), primary_key=True, index=True
    )
    meal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('meal.id'), primary_key=True, index=True
    )


class Meal(BaseModel):
    __tablename__ = 'meal'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey('event.id'), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    users: Mapped[list[Hacker]] = relationship('Hacker', secondary='hacker_meal')
