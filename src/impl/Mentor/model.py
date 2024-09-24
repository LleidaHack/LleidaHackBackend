from sqlalchemy import Column, ForeignKey, Integer, String
from src.impl.User.model import User
from src.utils import UserType
from sqlalchemy.orm import relationship


class Mentor(User):
    __tablename__ = 'mentor'
    user_id = Column(Integer, ForeignKey('my_user.id'), primary_key=True)
    github: str = Column(String, default="")
    linkedin: str = Column(String, default="")
    cv: str = Column(String, default="")
    location: str = Column(String, default="")
    how_did_you_meet_us: str = Column(String, default="")
    events = relationship('Event', secondary='mentor_event_participation')

    __mapper_args__ = {
        "polymorphic_identity": UserType.MENTOR.value,
        'with_polymorphic': '*'
    }
