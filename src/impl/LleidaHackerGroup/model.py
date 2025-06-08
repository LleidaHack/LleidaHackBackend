from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.LleidaHacker.model import LleidaHacker


class LleidaHackerGroupUser(BaseModel):
    __tablename__ = 'lleida_hacker_group_user'
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('lleida_hacker_group.id'), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('lleida_hacker.user_id'), primary_key=True
    )
    primary: Mapped[bool] = mapped_column(Boolean, default=False)


class LleidaHackerGroupLeader(BaseModel):
    __tablename__ = 'lleida_hacker_group_leader'
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('lleida_hacker_group.id'), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('lleida_hacker.user_id'), primary_key=True
    )


class LleidaHackerGroup(BaseModel):
    __tablename__ = 'lleida_hacker_group'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    image: Mapped[str] = mapped_column(String, default='')
    # members: Mapped[List["LleidaHacker"]] = relationship('LleidaHacker', secondary='group_lleida_hacker_user', backref='lleida_hacker_group')
    # members: Mapped[List["LleidaHacker"]] = relationship('LleidaHacker', back_populates='lleida_hacker_group')
    members: Mapped[list[LleidaHacker]] = relationship(
        'LleidaHacker', secondary='lleida_hacker_group_user'
    )
    leaders: Mapped[list[LleidaHacker]] = relationship(
        'LleidaHacker', secondary='lleida_hacker_group_leader'
    )
