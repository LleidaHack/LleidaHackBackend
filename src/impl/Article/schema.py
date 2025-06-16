from datetime import date
from typing import Optional

from pydantic import field_validator

from src.utils.Base.BaseSchema import BaseSchema


class ArticleGet(BaseSchema):
    id: int
    title: str
    content: str
    image: str
    creation_date: date
    edition_date: date
    owner_id: int


class ArticleGetAll(ArticleGet):
    pass


class ArticleCreate(BaseSchema):
    title: str
    content: str
    image: str

    @field_validator("title")
    @classmethod
    def title_validation(cls, v):
        if len(v) < 5:
            raise ValueError("title must be longer")
        return v

    @field_validator("content")
    @classmethod
    def content_validation(cls, v):
        if len(v) < 20:
            raise ValueError("content must be longer")
        return v


class ArticleUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_validation(cls, v):
        if len(v) < 5:
            raise ValueError("title must be longer")
        return v

    @field_validator("content")
    @classmethod
    def content_validation(cls, v):
        if len(v) < 20:
            raise ValueError("content must be longer")
        return v
