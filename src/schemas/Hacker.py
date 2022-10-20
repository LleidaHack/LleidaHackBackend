from schemas.User import User
from pydantic import BaseModel
from typing import List

class Hacker(User):
    banned: bool
    github: str
    linkedin: str

    class Config:
        orm_mode = True

class HackerGroup(BaseModel):
    name: str
    description: str
    members: List[Hacker]
    leader: int
    
    class Config:
        orm_mode = True