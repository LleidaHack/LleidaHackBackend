from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Notification import Notification as SchemaNotification

import services.notifications as notifications_service

router = APIRouter(
    prefix="/notification",
    tags=["Notification"],
)

@router.get("/{userId}")
async def get_notifications(userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return notifications_service.get_notifications(userId, db)

@router.post("/")
async def add_notification(payload:SchemaNotification, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_notification = notifications_service.add_notification(payload, db)
    return {"success": True, "created_id": new_notification.id}