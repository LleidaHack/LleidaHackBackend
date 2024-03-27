from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.impl.User.model import User
from src.utils.database import Base
from src.utils.UserType import UserType


class LleidaHacker(User):
    __tablename__ = 'lleida_hacker'
    user_id = Column(Integer, ForeignKey('my_user.id'), primary_key=True)
    role: str = (Column(String))
    nif: str = (Column(String, unique=True))
    student: bool = Column(Boolean, default=True)
    active: bool = Column(Boolean, default=True)
    github: str = Column(String)
    accepted: bool = (Column(Boolean, default=True))
    rejected: bool = (Column(Boolean, default=False))
    groups = relationship('LleidaHackerGroup',
                          secondary='lleida_hacker_group_user')
    events = relationship('Event',
                          secondary='lleida_hacker_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.LLEIDAHACKER.value,
    }