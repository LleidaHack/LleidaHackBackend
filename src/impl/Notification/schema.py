from utils.BaseSchema import BaseSchema
from typing import Optional


class Notification(BaseSchema):
    message: str


class NotificationUpdate(BaseSchema):
    message: Optional[str]
