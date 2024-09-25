from sqlalchemy.orm import Session

from src.impl.Notification.model import Notification
from src.utils.UserType import UserType


def get_notifications(userId: int, db: Session):
    return db.query(Notification).filter(Notification.user_id == userId).all()


def add_notification(payload: Notification, db: Session):
    new_notification = Notification(**payload.model_dump())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


def delete_notification(notificationId: int, db: Session):
    notification = db.query(Notification).filter(
        Notification.id == notificationId).first()
    db.delete(notification)
    db.commit()
    return notification
