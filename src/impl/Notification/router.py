from src.utils.database import get_db
from src.utils.Token import BaseToken
from src.utils.JWTBearer import JWTBearer

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from src.impl.Notification.schema import Notification as SchemaNotification

import src.impl.Notification.service as notifications_service

router = APIRouter(
    prefix="/notification",
    tags=["Notification"],
)


@router.get("/{userId}")
def get_notifications(userId: int,
                      response: Response,
                      db: Session = Depends(get_db),
                      str=Depends(JWTBearer())):
    return notifications_service.get_notifications(userId, db)


@router.post("/")
def add_notification(payload: SchemaNotification,
                     response: Response,
                     db: Session = Depends(get_db),
                     str=Depends(JWTBearer())):
    new_notification = notifications_service.add_notification(payload, db)
    return {"success": True, "user_id": new_notification.id}
