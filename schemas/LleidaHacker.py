from pydantic import BaseModel
from typing import List
from schemas.User import User

class LleidaHacker(User):
    role: str
    nif: str
    student: bool 
    active: bool 
    image: str 
    github: str 

class LleidaHackerGroup(BaseModel):
    name: str
    description: str
    members: List[LleidaHacker]
    # leader: int