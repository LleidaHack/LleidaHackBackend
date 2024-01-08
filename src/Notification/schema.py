from pydantic import BaseModel
from typing import Optional


class Notification(BaseModel):
    message: str

    class Config:
        orm_mode = True


class NotificationUpdate(BaseModel):
    message: Optional[str]
