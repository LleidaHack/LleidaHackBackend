from sqlalchemy.orm import Session

from models.Notification import Notification as ModelNotification
from models.UserType import UserType


async def get_notifications(userId: int, db: Session):
    return db.query(ModelNotification).filter(
        ModelNotification.user_id == userId).all()


async def add_notification(payload: ModelNotification, db: Session):
    new_notification = ModelNotification(**payload.dict())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


async def delete_notification(notificationId: int, db: Session):
    notification = db.query(ModelNotification).filter(
        ModelNotification.id == notificationId).first()
    db.delete(notification)
    db.commit()
    return notification
