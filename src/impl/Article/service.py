from fastapi_sqlalchemy import db

from src.error.NotFoundException import NotFoundException
from src.impl.Article.model import Article as ModelArticle

from src.utils.Base.BaseService import BaseService


class ArticleService(BaseService):
    name = 'article_service'
    
    def get_all(self):
        return db.session.query(ModelArticle).all()

    def get_by_id(self, articleId: int):
        article = db.session.query(ModelArticle).filter(
            ModelArticle.id == articleId).first()
        if article is None:
            raise NotFoundException('article not found')
        return article