from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.impl.User.model import User
from src.utils import UserType

if TYPE_CHECKING:
    from src.impl.Event.model import Event


class Mentor(User):
    __tablename__ = 'mentor'
    user_id: Mapped[int] = mapped_column(ForeignKey('my_user.id'), primary_key=True)
    github: Mapped[str] = mapped_column(String, default="")
    linkedin: Mapped[str] = mapped_column(String, default="")
    cv: Mapped[str] = mapped_column(String, default="")
    location: Mapped[str] = mapped_column(String, default="")
    how_did_you_meet_us: Mapped[str] = mapped_column(String, default="")
    events: Mapped[List["Event"]] = relationship('Event', secondary='mentor_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.MENTOR.value,
        'with_polymorphic': '*'
    }
