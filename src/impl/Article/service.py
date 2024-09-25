from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Article.model import Article
from src.impl.Article.schema import ArticleCreate, ArticleUpdate
from src.impl.ArticleType.service import ArticleTypeService
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class ArticleService(BaseService):
    name = 'article_service'
    article_type_service: ArticleTypeService = None

    def get_all(self):
        return db.session.query(Article).all()

    def get_by_id(self, articleId: int):
        article = db.session.query(Article).filter(
            Article.id == articleId).first()
        if article is None:
            raise NotFoundException('article not found')
        return article

    def create(self, article: ArticleCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to add articles")
        db_article = Article(**article.model_dump(), owner_id=data.user_id)
        db.session.add(db_article)
        db.session.commit()
        db.session.refresh(db_article)
        return db_article

    def update(self, id: int, article: ArticleUpdate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to update articles")
        db_article = self.get_by_id(id)
        set_existing_data(db_article, article)
        db.session.commit()
        db.session.refresh(db_article)
        return db_article

    def delete(self, id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to delete articles")
        db_article = self.get_by_id(id)
        db.session.delete(db_article)
        db.session.commit()
        return db_article

    @BaseService.needs_service(ArticleTypeService)
    def add_type(self, article_id: int, type_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to change an article's type")
        article = self.get_by_id(article_id)
        type = self.article_type_service.get_by_id(type_id)
        if type in article.types:
            raise InvalidDataException('this article already has this type')
        article.types.append(type)
        db.session.commit()
        db.session.refresh(article)
        return article

    @BaseService.needs_service(ArticleTypeService)
    def delete_type(self, article_id: int, type_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to change an article's type")
        article = self.get_by_id(article_id)
        type = self.article_type_service.get_by_id(type_id)
        if type not in article.types:
            raise InvalidDataException("this article doesn't have this type")
        article.types.remove(type)
        db.session.commit()
        db.session.refresh(article)
        return article
