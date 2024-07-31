from datetime import date
from typing import Optional
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

class ArticleUpdate(BaseSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None