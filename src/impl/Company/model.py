from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.utils.Base.BaseModel import BaseModel



class Company(BaseModel):
    __tablename__ = 'company'
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    description: str = Column(String)
    address: str = Column(String)
    telephone: str = Column(String)
    website: str = Column(String)
    image: str = Column(String)
    # is_image_url: bool = Column(Boolean, default=False)
    linkdin: str = Column(String)
    leader_id: int = Column(Integer, ForeignKey('my_user.id'))
    users = relationship('User', secondary='company_user')
    events = relationship('Event', secondary='company_event_participation')
