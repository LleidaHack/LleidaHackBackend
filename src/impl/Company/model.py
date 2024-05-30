# from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.impl.CompanyUser.model import CompanyUser
from src.impl.Event.model import CompanyParticipation
# from src.impl.Event.model import Event
from src.impl.User.model import User
# from src.utils.Base.BaseModel import BaseModel

from sqlmodel import Field, Relationship, SQLModel
class Company(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    address: str
    telephone: str
    website: str
    image: str
    # is_image_url: bool = Column(Boolean, default=False)
    linkdin: str
    leader_id: int = Field(foreign_key='my_user.id')
    # users: list['User'] = Relationship(link_model=CompanyUser)
    # events: list['Event'] = Relationship(link_model=CompanyParticipation)
