from sqlalchemy.orm import Session

from src.Notification.model import Notification as ModelNotification
from src.Utils.UserType import UserType


def get_notifications(userId: int, db: Session):
    return db.query(ModelNotification).filter(
        ModelNotification.user_id == userId).all()


def add_notification(payload: ModelNotification, db: Session):
    new_notification = ModelNotification(**payload.dict())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


def delete_notification(notificationId: int, db: Session):
    notification = db.query(ModelNotification).filter(
        ModelNotification.id == notificationId).first()
    db.delete(notification)
    db.commit()
    return notification
