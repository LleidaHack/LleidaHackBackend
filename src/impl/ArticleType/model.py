from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.impl.Article.model import Article
from src.utils.Base.BaseModel import BaseModel


class ArticleType(BaseModel):
    __tablename__ = 'article_type'
    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, unique=True, index=True)
    description: str = Column(String)

    articles: List[Article] = relationship('Article',
                                           secondary='article_article_type',
                                           primaryjoin='ArticleType.id == article_article_type.article_type_id', 
                                           secondaryjoin='Article.id == article_article_type.article_id', 
                                           uselist=True)