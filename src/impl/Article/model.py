from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.impl.User.model import User
from src.utils.Base.BaseModel import BaseModel

if TYPE_CHECKING:
    from src.impl.ArticleType.model import ArticleType


class ArticleArticleType(BaseModel):
    __tablename__ = 'article_article_type'
    article_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('article.id'), primary_key=True
    )
    article_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('article_type.id'), primary_key=True
    )


class Article(BaseModel):
    __tablename__ = 'article'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    image: Mapped[str] = mapped_column(String, default='')
    creation_date: Mapped[date] = mapped_column(DateTime, default=func.now())
    edition_date: Mapped[date] = mapped_column(DateTime, default=func.now())
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('my_user.id'))

    owner: Mapped[User] = relationship('User')
    types: Mapped[list[ArticleType]] = relationship(
        'ArticleType',
        'article_article_type',
        primaryjoin='Article.id == article_article_type.c.article_id',
        secondaryjoin='ArticleType.id == article_article_type.c.article_type_id',
        uselist=True,
    )
