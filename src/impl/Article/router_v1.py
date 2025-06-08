from fastapi import APIRouter

from src.impl.Article.schema import (
    ArticleCreate,
    ArticleGet,
    ArticleGetAll,
    ArticleUpdate,
)
from src.impl.Article.service import ArticleService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/article',
    tags=['Article'],
)

article_service: ArticleService = ArticleService()


@router.get('/all', response_model=list[ArticleGet])
def get_all():
    return article_service.get_all()


@router.get('/{article_id}', response_model=ArticleGetAll | ArticleGet)
def get_by_id(article_id: int):
    return article_service.get_by_id(article_id)


@router.put('/{article_id}')
def update(article_id: int, payload: ArticleUpdate, token: BaseToken = jwt_dependency):
    article, updated = article_service.update(article_id, payload, token)
    return {'success': True, 'updated_id': article.id, 'updated': updated}


@router.post('/')
def create(payload: ArticleCreate, token: BaseToken = jwt_dependency):
    article = article_service.create(payload, token)
    return {'success': True, 'created_id': article.id}


@router.delete('/{article_id}')
def delete(article_id: int, token: BaseToken = jwt_dependency):
    article = article_service.delete(article_id, token)
    return {'success': True, 'deleted_id': article.id}


@router.put('/{article_id}/add/{type_id}')
def add_type(article_id: int, type_id: int, token: BaseToken = jwt_dependency):
    article_service.add_type(article_id, type_id, token)
    return {'success': True, 'updated_article_id': article_id, 'added_type_id': type_id}


@router.put('/{article_id}/delete/{type_id}')
def delete_type(article_id: int, type_id: int, token: BaseToken = jwt_dependency):
    article_service.delete_type(article_id, type_id, token)
    return {
        'success': True,
        'updated_article_id': article_id,
        'deleted_type_id': type_id,
    }
