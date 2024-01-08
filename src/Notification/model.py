from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from database import Base
from src.Event.model import Event
from src.User.model import User


class Notification(Base):
    __tablename__ = 'notification'
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey('user.id'))
    message: str = Column(String)
    read: bool = Column(Boolean, default=False)
    created_at: str = Column(String)
    updated_at: str = Column(String)
    deleted_at: str = Column(String)
    is_mail: bool = Column(Boolean, default=True)
    deleted: bool = Column(Boolean, default=False)
    type: str = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "polymorphic_on": type,
    }


class HackerAcceptedNotification(Notification):
    __tablename__ = 'hacker_accepted_notification'
    id: int = Column(Integer,
                     ForeignKey('notification.id'),
                     primary_key=True,
                     index=True)
    event_id: int = Column(Integer, ForeignKey('event.id'))
    __mapper_args__ = {
        "polymorphic_identity": "hacker_accepted_notification",
    }


class HackerRejectedNotification(Notification):
    __tablename__ = 'hacker_rejected_notification'
    id: int = Column(Integer,
                     ForeignKey('notification.id'),
                     primary_key=True,
                     index=True)
    event_id: int = Column(Integer, ForeignKey('event.id'))
    __mapper_args__ = {
        "polymorphic_identity": "hacker_rejected_notification",
    }


class LleidaHackerAcceptedNotification(Notification):
    __tablename__ = 'lleida_hacker_accepted_notification'
    id: int = Column(Integer,
                     ForeignKey('notification.id'),
                     primary_key=True,
                     index=True)
    __mapper_args__ = {
        "polymorphic_identity": "lleida_hacker_accepted_notification",
    }


class LleidaHackerRejectedNotification(Notification):
    __tablename__ = 'lleida_hacker_rejected_notification'
    id: int = Column(Integer,
                     ForeignKey('notification.id'),
                     primary_key=True,
                     index=True)
    __mapper_args__ = {
        "polymorphic_identity": "lleida_hacker_rejected_notification",
    }
