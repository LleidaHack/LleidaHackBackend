from fastapi_sqlalchemy import db

from src.error.NotFoundException import NotFoundException
from src.impl.ArticleType.model import ArticleType as ModelArticleType
from src.utils.Base.BaseService import BaseService


class ArticleTypeService(BaseService):
    name = 'article_type_service'
    
    def get_all(self):
        return db.session.query(ModelArticleType).all()

    def get_by_id(self, articleTypeId: int):
        articleType = db.session.query(ModelArticleType).filter(
            ModelArticleType.id == articleTypeId).first()
        if articleType is None:
            raise NotFoundException('article type not found')
        return articleType