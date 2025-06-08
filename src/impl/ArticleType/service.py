from fastapi_sqlalchemy import db

from src.error.AuthenticationError import AuthenticationError
from src.error.NotFoundError import NotFoundError
from src.impl.ArticleType.model import ArticleType
from src.impl.ArticleType.schema import ArticleTypeCreate, ArticleTypeUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class ArticleTypeService(BaseService):
    name = 'article_type_service'

    def get_all(self):
        return db.session.query(ArticleType).all()

    def get_by_id(self, item_id: int):
        article_type = (
            db.session.query(ArticleType).filter(ArticleType.id == id).first()
        )
        if article_type is None:
            raise NotFoundError('article type not found')
        return article_type

    def create(self, article_type: ArticleTypeCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('You are not allowed to add article types')
        db_article_type = ArticleType(
            **article_type.model_dump(), owner_id=data.user_id
        )
        db.session.add(db_article_type)
        db.session.commit()
        db.session.refresh(db_article_type)
        return db_article_type

    def update(
        self, article_type_id: int, article_type: ArticleTypeUpdate, data: BaseToken
    ):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('You are not allowed to update article types')
        db_article_type = self.get_by_id(article_type_id)
        set_existing_data(db_article_type, article_type)
        db.session.commit()
        db.session.refresh(db_article_type)
        return db_article_type

    def delete(self, article_type_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('You are not allowed to delete article types')
        db_article_type = self.get_by_id(article_type_id)
        db.session.delete(db_article_type)
        db.session.commit()
        return db_article_type
