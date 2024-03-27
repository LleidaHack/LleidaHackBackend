from typing import Optional

from src.utils.Base.BaseSchema import BaseSchema


class CompanyCreate(BaseSchema):
    name: str
    description: str
    website: str
    image: Optional[str] = None
    is_image_url: Optional[bool] = None
    address: str
    linkdin: str
    telephone: str


class CompanyGet(BaseSchema):
    name: str
    description: str
    website: str
    image: str
    is_image_url: bool
    address: str
    linkdin: str
    telephone: str


class CompanyGetAll(CompanyGet):
    pass


class CompanyUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    image: Optional[str] = None
    is_image_url: Optional[bool] = None
    address: Optional[str] = None
    linkdin: Optional[str] = None
    telephone: Optional[str] = None
