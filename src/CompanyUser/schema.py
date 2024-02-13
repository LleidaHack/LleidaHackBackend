from typing import Optional
from src.User.schema import UserGet, UserGetAll, UserUpdate

class CompanyUserGet(UserGet):
    role: str
    company_id: int

class CompanyUserGetAll(UserGetAll):
    pass

class CompanyUserUpdate(UserUpdate):
    role: Optional[str]
    company_id: Optional[int]
