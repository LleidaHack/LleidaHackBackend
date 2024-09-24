from typing import Optional
from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class CompanyCreate(BaseSchema):
    name: str
    description: str
    website: str
    image: Optional[str] = None
    tier: int
    #is_image_url: Optional[bool] = None
    address: str
    linkdin: str
    telephone: str

    @field_validator('tier')
    @classmethod
    def tier_validator(cls, v):
        if v < 0:
            raise ValueError('tier must be a positive integer')
        return v


class CompanyGet(BaseSchema):
    id: int
    name: str
    description: str
    website: str
    image: str
    tier: int
    #is_image_url: bool
    address: str
    linkdin: str
    telephone: str


class CompanyGetAll(CompanyGet):
    id: int


class CompanyUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    image: Optional[str] = None
    tier: Optional[int] = None
    #is_image_url: Optional[bool] = None
    address: Optional[str] = None
    linkdin: Optional[str] = None
    telephone: Optional[str] = None

    @field_validator('tier')
    @classmethod
    def tier_validator(cls, v):
        if v < 0:
            raise ValueError('tier must be a positive integer')
        return v
