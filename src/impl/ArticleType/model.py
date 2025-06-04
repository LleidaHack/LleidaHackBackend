from typing import List, TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.Article.model import Article


class ArticleType(BaseModel):
    __tablename__ = 'article_type'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(String)

    articles: Mapped[List["Article"]] = relationship(
        'Article',
        secondary='article_article_type',
        primaryjoin='ArticleType.id == article_article_type.c.article_type_id',
        secondaryjoin='Article.id == article_article_type.c.article_id',
        uselist=True)
