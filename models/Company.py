from typing import List
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
from models.User import User

class Company(Base):
    __tablename__ = 'company'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    address: str = Column(String)
    telephone: str = Column(String)
    website: str = Column(String)
    logo: str = Column(String)
    users: List[User] = relationship('User', secondary='company_user')
    # events: List[Event] = relationship('Event', secondary='sponsor')