

from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.ArticleType.schema import (ArticleTypeCreate, ArticleTypeGet, ArticleTypeGetAll,
                                         ArticleTypeUpdate)
from src.impl.ArticleType.service import ArticleTypeService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/article_type",
    tags=["ArticleType"],
)

article_type_service : ArticleTypeService = ArticleTypeService() 

@router.get("/all", response_model=List[ArticleTypeGet])
def get_all():
    return article_type_service.get_all()

@router.get("/{id}",
            response_model=Union[ArticleTypeGetAll, ArticleTypeGet])
def get():
    return article_type_service.get(id)

@router.put("/{id}")
def update(id: int,
           payload: ArticleTypeUpdate,
           token: BaseToken = Depends(JWTBearer())):
    article_type, updated = article_type_service.update(id, payload, token)
    return {"success": True, "updated_id": article_type.id, "updated": updated}

@router.post("/")
def create(payload: ArticleTypeCreate, token: BaseToken = Depends(JWTBearer())):
    article_type = article_type_service.create(payload, token)
    return {"success": True, "created_id": article_type.id}

@router.delete("/{id}")
def delete(id: int, token: BaseToken = Depends(JWTBearer())):
    article_type = article_type_service.delete(id, token)
    return {"success": True, "deleted_id": article_type.id}
