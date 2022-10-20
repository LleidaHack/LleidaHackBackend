from pydantic import BaseModel

class Notification(BaseModel):
    message: str

    class Config:
        orm_mode = True