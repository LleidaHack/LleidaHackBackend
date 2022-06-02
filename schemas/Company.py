from pydantic import BaseModel
from typing import List
from schemas.User import User

class Company(BaseModel):
    name: str
    description: str
    website: str
    logo: str
    address: str
    telephone: str
    users: List[User]
    # events: List[Event]

    # class Config:
        # orm_mode = True