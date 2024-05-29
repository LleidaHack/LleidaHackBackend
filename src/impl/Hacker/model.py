from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship
from src.impl.Event.model import Event, HackerParticipation
from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser

from src.impl.User.model import User
from src.utils.UserType import UserType


class Hacker(User):
    __tablename__ = 'hacker'
    user_id: int = Field(foreign_key='my_user.id', primary_key=True)
    # banned: bool = Column(Integer, default=0)
    banned: bool = Field(default=False)
    github: str = Field(default="")
    linkedin: str = Field(default="")
    cv: str = Field(default="")
    studies: str = Field(default="")
    study_center: str = Field(default="")
    location: str = Field(default="")
    how_did_you_meet_us: str = Field(default="")
    groups: 'HackerGroup' = Relationship(link_model=HackerGroupUser)
    # is_leader: bool = Column(Integer, default=0)
    events: 'Event' = Relationship(link_model=HackerParticipation)

    __mapper_args__ = {
        "polymorphic_identity": UserType.HACKER.value,
        'with_polymorphic': '*'
    }
