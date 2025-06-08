from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class CompanyCreate(BaseSchema):
    name: str
    description: str
    website: str
    image: str | None = None
    tier: int
    # is_image_url: Optional[bool] = None
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
    # is_image_url: bool
    address: str
    linkdin: str
    telephone: str


class CompanyGetAll(CompanyGet):
    id: int


class CompanyUpdate(BaseSchema):
    name: str | None = None
    description: str | None = None
    website: str | None = None
    image: str | None = None
    tier: int | None = None
    # is_image_url: Optional[bool] = None
    address: str | None = None
    linkdin: str | None = None
    telephone: str | None = None

    @field_validator('tier')
    @classmethod
    def tier_validator(cls, v):
        if v < 0:
            raise ValueError('tier must be a positive integer')
        return v
