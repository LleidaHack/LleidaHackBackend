from pydantic import BaseModel
from typing import List
from schemas.User import User

class LleidaHacker(User):
    role: str
    nif: str
    student: bool 
    active: bool
    github: str
    # linkedin: str

    class Config:
        orm_mode = True

class LleidaHackerGroup(BaseModel):
    name: str
    description: str
    members: List[LleidaHacker]
    # leader: int

    class Config:
        orm_mode = True