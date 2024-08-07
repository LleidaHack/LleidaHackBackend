from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.ArticleType.model import ArticleType as ModelArticleType
from src.impl.ArticleType.schema import ArticleTypeCreate, ArticleTypeUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class ArticleTypeService(BaseService):
    name = 'article_type_service'
    
    def get_all(self):
        return db.session.query(ModelArticleType).all()

    def get_by_id(self, id: int):
        article_type = db.session.query(ModelArticleType).filter(
            ModelArticleType.id == id).first()
        if article_type is None:
            raise NotFoundException('article type not found')
        return article_type
    
    def create(self, article_type: ArticleTypeCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to add article types")
        db_article_type = ModelArticleType(**article_type.dict(), owner_id=data.user_id)
        db.session.add(db_article_type)
        db.session.commit()
        db.session.refresh(db_article_type)
        return db_article_type

    def update(self, id: int, article_type: ArticleTypeUpdate,
                    data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to update article types")
        db_article_type = self.get_by_id(id)
        set_existing_data(db_article_type, article_type)
        db.session.commit()
        db.session.refresh(db_article_type)
        return db_article_type
    
    def delete(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to delete article types")
        db_article_type = self.get_by_id(id)
        db.session.delete(db_article_type)
        db.session.commit()
        return db_article_type