from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship, SQLModel
from src.impl.User.model import User
from src.utils.Base.BaseModel import BaseModel


class HackerGroupUser(SQLModel, table=True):
    __tablename__ = 'hacker_group_user'
    hacker_id: int = Field(foreign_key='hacker.user_id', primary_key=True)
    group_id: int = Field(foreign_key='hacker_group.id', primary_key=True)


class HackerGroup(SQLModel, table=True):
    __tablename__ = 'hacker_group'
    id: int = Field(primary_key=True, index=True)
    code: str = Field(unique=True, index=True)
    name: str
    description: str
    leader_id: int = Field(foreign_key='hacker.user_id', nullable=False)
    event_id: int = Field(foreign_key='event.id', nullable=False)
    # event: Event = relationship('Event', secondary='hacker_event')
    members: list['User'] = Relationship(
        link_model=HackerGroupUser, sa_relationship_args=
        {'primaryjoin': "HackerGroup.id==hacker_group_user.c.group_id",
        'secondaryjoin': "User.id==hacker_group_user.c.hacker_id"})
