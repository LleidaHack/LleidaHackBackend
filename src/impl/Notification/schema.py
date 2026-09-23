from src.utils.Base.BaseSchema import BaseSchema


class Notification(BaseSchema):
    message: str


class NotificationUpdate(BaseSchema):
    message: str | None = None
