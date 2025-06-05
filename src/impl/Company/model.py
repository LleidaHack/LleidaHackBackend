from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.User.model import User
    from src.impl.Event.model import Event


class Company(BaseModel):
    __tablename__ = 'company'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)
    address: Mapped[Optional[str]] = mapped_column(String)
    telephone: Mapped[Optional[str]] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String)
    image: Mapped[Optional[str]] = mapped_column(String)
    tier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # is_image_url: Mapped[bool] = mapped_column(Boolean, default=False)
    linkdin: Mapped[Optional[str]] = mapped_column(String)
    leader_id: Mapped[Optional[int]] = mapped_column(Integer,
                                                     ForeignKey('my_user.id'))

    # Relationships
    users: Mapped[List["User"]] = relationship('User',
                                               secondary='company_user')
    events: Mapped[List["Event"]] = relationship(
        'Event', secondary='company_event_participation')
