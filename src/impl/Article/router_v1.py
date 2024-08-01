

from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Article.schema import ArticleGet, ArticleGetAll, ArticleUpdate
from src.impl.Article.service import ArticleService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/article",
    tags=["Article"],
)

article_service : ArticleService = ArticleService() 

@router.get("/all", response_model=List[ArticleGet])
def get_all():
    return article_service.get_all()

@router.get("/{id}",
            response_model=Union[ArticleGetAll, ArticleGet])
def get():
    return article_service.get(id)

@router.put("/{id}")
def update(id: int,
           payload: ArticleUpdate,
           token: BaseToken = Depends(JWTBearer())):
    article, updated = article_service.update(id, payload, token)
    return {"success": True, "updated_id": article.id, "updated": updated}

@router.post("/{id}")
def create(id: int, token: BaseToken = Depends(JWTBearer())):
    article = article_service.create(id, token)
    return {"success": True, "created_id": article.id}

@router.delete("/{id}")
def delete(id: int, token: BaseToken = Depends(JWTBearer())):
    article = article_service.delete(id, token)
    return {"success": True, "deleted_id": article.id}

@router.put("/{article_id}/{type_id}")
def add_type(article_id: int, type_id: int, token: BaseToken = Depends(JWTBearer())):
    article_service.add_type(article_id, type_id, token)
    return {"success": True, "updated_article_id": article_id, "added_type_id": type_id}

@router.put("/{article_id}/{type_id}")
def delete_type(article_id: int, type_id: int, token: BaseToken = Depends(JWTBearer())):
    article_service.delete_type(article_id, type_id, token)
    return {"success": True, "updated_article_id": article_id, "deleted_type_id": type_id}