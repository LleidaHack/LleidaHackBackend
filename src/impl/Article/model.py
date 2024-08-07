from datetime import date

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from src.impl.User.model import User
from src.utils.Base.BaseModel import BaseModel


class ArticleArticleType(BaseModel):
    __tablename__ = 'article_article_type'
    article_id: int = Column(Integer,
                             ForeignKey('article.id'),
                             primary_key=True)
    article_type_id: int = Column(Integer,
                                  ForeignKey('article_type.id'),
                                  primary_key=True)


class Article(BaseModel):
    __tablename__ = 'article'
    id: int = Column(Integer, primary_key=True)
    title: str = Column(String)
    content: str = Column(String)
    image: str = Column(String, default='')
    creation_date: date = Column(DateTime, default=func.now())
    edition_date: date = Column(DateTime, default=func.now())
    owner_id: int = Column(Integer, ForeignKey('my_user.id'), nullable=False)

    owner: User = relationship('User')
    types = relationship(
        'ArticleType',
        'article_article_type',
        primaryjoin='Article.id == article_article_type.article_id',
        secondaryjoin='ArticleType.id == article_article_type.id',
        uselist=True)
