from typing import Optional

from utils.BaseSchema import BaseSchema


class CompanyCreate(BaseSchema):
    name: str
    description: str
    website: str
    image: Optional[str]
    is_image_url: Optional[bool]
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
    name: Optional[str]
    description: Optional[str]
    website: Optional[str]
    image: Optional[str]
    is_image_url: Optional[bool]
    address: Optional[str]
    linkdin: Optional[str]
    telephone: Optional[str]