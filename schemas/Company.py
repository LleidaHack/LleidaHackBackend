from pydantic import BaseModel
from typing import List
from schemas.User import User
from schemas.Event import Event


class Company(BaseModel):
    name: str
    description: str
    website: str
    logo: str
    address: str
    linkdin: str
    telephone: str
    #users: List[User]
    events: List[Event]

    # class Config:
    #     orm_mode = True


class CompanyUser(User):
    role: str
    company_id: int

    # class Config:
    #     orm_mode = True
