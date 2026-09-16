from pydantic import ConfigDict

from src.impl.User.schema import UserCreate, UserGet, UserGetAll, UserUpdate


class CompanyUserCreate(UserCreate):
    role: str
    company_id: int
    active: int


class CompanyUserGet(UserGet):
    role: str
    company_id: int


class CompanyUserGetAll(UserGetAll):
    active: bool
    pass


class CompanyUserUpdate(UserUpdate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
