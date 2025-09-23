from fastapi import APIRouter, Depends, Response

import src.impl.Notification.service as notifications_service
from src.impl.Notification.schema import Notification
from src.utils.JWTBearer import JWTBearer

router = APIRouter(
    prefix="/notification",
    tags=["Notification"],
)


@router.get("/{userId}")
def get_notifications(userId: int, response: Response, str=Depends(JWTBearer())):
    return notifications_service.get_notifications(userId)


@router.post("/")
def add_notification(
    payload: Notification, response: Response, str=Depends(JWTBearer())
):
    new_notification = notifications_service.add_notification(payload)
    return {"success": True, "user_id": new_notification.id}
