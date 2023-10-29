from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

from sqlalchemy.orm import deferred
from sqlalchemy.orm import Mapped

class Medal(Base):
    __tablename__ = 'medal'
    id = Column(Integer, primary_key=True) 
    name: str = Column(String)
    description: str = Column(String)
    condition: str = Column(String) #Ton in $user.name
    image: str = Column(String)

