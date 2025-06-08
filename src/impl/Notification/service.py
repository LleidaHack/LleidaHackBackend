from sqlalchemy.orm import Session

from src.impl.Notification.model import Notification


def get_notifications(user_id: int, db: Session):
    return db.query(Notification).filter(Notification.user_id == user_id).all()


def add_notification(payload: Notification, db: Session):
    new_notification = Notification(**payload.model_dump())
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


def delete_notification(notification_id: int, db: Session):
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )
    db.delete(notification)
    db.commit()
    return notification
