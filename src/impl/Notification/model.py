from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.utils.Base.BaseModel import BaseModel


class Notification(BaseModel):
    __tablename__ = 'notification'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('my_user.id'))
    message: Mapped[str] = mapped_column(String)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)
    deleted_at: Mapped[str] = mapped_column(String)
    is_mail: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    type: Mapped[str] = mapped_column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'my_user',
        'polymorphic_on': type,
    }


class HackerAcceptedNotification(Notification):
    __tablename__ = 'hacker_accepted_notification'
    id: Mapped[int] = mapped_column(
        ForeignKey('notification.id'), primary_key=True, index=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey('event.id'))
    __mapper_args__ = {
        'polymorphic_identity': 'hacker_accepted_notification',
    }


class HackerRejectedNotification(Notification):
    __tablename__ = 'hacker_rejected_notification'
    id: Mapped[int] = mapped_column(
        ForeignKey('notification.id'), primary_key=True, index=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey('event.id'))
    __mapper_args__ = {
        'polymorphic_identity': 'hacker_rejected_notification',
    }


class LleidaHackerAcceptedNotification(Notification):
    __tablename__ = 'lleida_hacker_accepted_notification'
    id: Mapped[int] = mapped_column(
        ForeignKey('notification.id'), primary_key=True, index=True
    )
    __mapper_args__ = {
        'polymorphic_identity': 'lleida_hacker_accepted_notification',
    }


class LleidaHackerRejectedNotification(Notification):
    __tablename__ = 'lleida_hacker_rejected_notification'
    id: Mapped[int] = mapped_column(
        ForeignKey('notification.id'), primary_key=True, index=True
    )
    __mapper_args__ = {
        'polymorphic_identity': 'lleida_hacker_rejected_notification',
    }
