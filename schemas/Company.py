from pydantic import BaseModel
from typing import Optional
from schemas.User import User, UserUpdate
# from schemas.Event import Event


class Company(BaseModel):
    name: str
    description: str
    website: str
    logo: str
    address: str
    linkdin: str
    telephone: str

    # class Config:
    #     orm_mode = True


class CompanyUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    website: Optional[str]
    logo: Optional[str]
    address: Optional[str]
    linkdin: Optional[str]
    telephone: Optional[str]


class CompanyUser(User):
    role: str
    company_id: int

    # class Config:
    #     orm_mode = True


class CompanyUserUpdate(UserUpdate):
    role: Optional[str]
    company_id: Optional[int]
