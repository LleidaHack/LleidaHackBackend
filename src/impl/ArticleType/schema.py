from typing import Optional
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
    
class ArticleTypeUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    