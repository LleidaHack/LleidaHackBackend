
from typing import Optional

from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class ArticleTypeGet(BaseSchema):
    id: int
    name: str
    description: str

class ArticleTypeGetAll(ArticleTypeGet):
    pass

class ArticleTypeCreate(BaseSchema):
    name: str
    description: str

    @field_validator('name')
    @classmethod
    def name_validation(cls,v):
        if len(v) < 3:
            raise ValueError('name must be longer')
        return v

    @field_validator('description')
    @classmethod
    def description_validation(cls,v):
        if len(v) < 10:
            raise ValueError('description must be longer')
        return v

    
class ArticleTypeUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_validation(cls,v):
        if len(v) < 3:
            raise ValueError('name must be longer')
        return v

    @field_validator('description')
    @classmethod
    def description_validation(cls,v):
        if len(v) < 10:
            raise ValueError('description must be longer')
        return v
    