from __future__ import annotations
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship, deferred, Mapped

from database import Base

from src.impl.User.model import User
from src.Utils.UserType import UserType


class Hacker(User):
    __tablename__ = 'hacker'
    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    banned: bool = (Column(Integer, default=0))
    github: str = Column(String)
    linkedin: str = Column(String)
    cv: str = (Column(String))
    studies: str = (Column(String, default=""))
    study_center: str = (Column(String, default=""))
    location: str = (Column(String, default=""))
    how_did_you_meet_us: str = (Column(String, default=""))
    groups = relationship('HackerGroup', secondary='hacker_group_user')
    # is_leader: bool = Column(Integer, default=0)
    events = relationship('Event', secondary='hacker_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.HACKER.value,
    }
