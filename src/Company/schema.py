from pydantic import BaseModel
from typing import Optional


class CompanyGet(BaseModel):
    name: str
    description: str
    website: str
    image: Optional[str]
    is_image_url: Optional[bool]
    address: str
    linkdin: str
    telephone: str

class CompanyGetAll(CompanyGet):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    website: Optional[str]
    image: Optional[str]
    is_image_url: Optional[bool]
    address: Optional[str]
    linkdin: Optional[str]
    telephone: Optional[str]