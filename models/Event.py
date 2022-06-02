from datetime import date
from typing import List
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
# class Event(Base):
#     __tablename__ = 'llhk_event'
#     id: int = Column(Integer, primary_key=True, index=True)
#     name: str = Column(String)
#     date: date = Column(DateTime, default=func.now())
#     users: List[User] = relationship('User', secondary='llhk_user_event')
#     location: str = Column(String)
#     sponsors: List[Company] = relationship('Company', secondary='sponsor')
#     archived: bool = Column(Integer, default=0)
#     description: str = Column(String)
#     status: int = Column(Integer, default=0)
