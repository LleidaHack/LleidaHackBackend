from pydantic import BaseModel

class Notification(BaseModel):
    message: str