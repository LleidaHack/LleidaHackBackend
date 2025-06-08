from fastapi import APIRouter

from src.impl.ArticleType.schema import (
    ArticleTypeCreate,
    ArticleTypeGet,
    ArticleTypeGetAll,
    ArticleTypeUpdate,
)
from src.impl.ArticleType.service import ArticleTypeService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/article_type',
    tags=['ArticleType'],
)

article_type_service: ArticleTypeService = ArticleTypeService()


@router.get('/all', response_model=list[ArticleTypeGet])
def get_all():
    return article_type_service.get_all()


@router.get('/{article_type_id}', response_model=ArticleTypeGetAll | ArticleTypeGet)
def get(article_type_id: int):
    return article_type_service.get(article_type_id)


@router.put('/{article_type_id}')
def update(
    article_type_id: int, payload: ArticleTypeUpdate, token: BaseToken = jwt_dependency
):
    article_type, updated = article_type_service.update(article_type_id, payload, token)
    return {'success': True, 'updated_id': article_type.id, 'updated': updated}


@router.post('/')
def create(payload: ArticleTypeCreate, token: BaseToken = jwt_dependency):
    article_type = article_type_service.create(payload, token)
    return {'success': True, 'created_id': article_type.id}


@router.delete('/{article_type_id}')
def delete(article_type_id: int, token: BaseToken = jwt_dependency):
    article_type = article_type_service.delete(article_type_id, token)
    return {'success': True, 'deleted_id': article_type.id}
