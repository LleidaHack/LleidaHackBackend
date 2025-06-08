from fastapi import APIRouter, Response

import src.impl.Notification.service as notifications_service
from src.impl.Notification.schema import Notification
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/notification',
    tags=['Notification'],
)


@router.get('/{user_id}')
def get_notifications(
    user_id: int, response: Response, token: BaseToken = jwt_dependency
):
    return notifications_service.get_notifications(user_id)


@router.post('/')
def add_notification(
    payload: Notification, response: Response, token: BaseToken = jwt_dependency
):
    new_notification = notifications_service.add_notification(payload)
    return {'success': True, 'user_id': new_notification.id}
