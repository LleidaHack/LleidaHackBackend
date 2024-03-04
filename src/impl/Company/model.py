from __future__ import annotations
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.utils.database import Base


class Company(Base):
    __tablename__ = 'company'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    address: str = Column(String)
    telephone: str = Column(String)
    website: str = Column(String)
    image: str = Column(String)
    is_image_url: bool = Column(Boolean, default=False)
    linkdin: str = Column(String)
    leader_id: int = Column(Integer, ForeignKey('user.id'))
    users = relationship('User', secondary='company_user')
    events = relationship('Event', secondary='company_event_participation')
