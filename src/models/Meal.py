from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from models.Hacker import Hacker as ModelHacker

from database import Base

class HackerMeal(Base):
    __tablename__ = "hacker_meal"
    user_id = Column(Integer, ForeignKey("hacker.user_id"), primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meal.id"), primary_key=True, index=True)
    
class Meal(Base):
    __tablename__ = 'meal'
    id: int = Column(Integer, primary_key=True, index=True)
    event_id: int = Column(Integer, ForeignKey('llhk_event.id'), index=True)
    name: str = Column(String)
    description: str = Column(String)
    users: List[ModelHacker] = relationship('Hacker', secondary='hacker_meal')