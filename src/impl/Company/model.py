from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.Event.model import Event
    from src.impl.User.model import User


class Company(BaseModel):
    __tablename__ = 'company'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    telephone: Mapped[str | None] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)
    image: Mapped[str | None] = mapped_column(String)
    tier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # is_image_url: Mapped[bool] = mapped_column(Boolean, default=False)
    linkdin: Mapped[str | None] = mapped_column(String)
    leader_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('my_user.id'))

    # Relationships
    users: Mapped[list[User]] = relationship('User', secondary='company_user')
    events: Mapped[list[Event]] = relationship(
        'Event', secondary='company_event_participation'
    )
