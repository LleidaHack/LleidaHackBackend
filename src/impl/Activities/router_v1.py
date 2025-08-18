from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Activity.schema import (
    ActivityCreate,
    ActivityGet,
    ActivityUpdate,
)
from src.impl.Activity.service import ActivityService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/activity",
    tags=["Activity"],
)

activity_service: ActivityService = ActivityService()


@router.get("/all", response_model=List[ActivityGet])
def get_all():
    return activity_service.get_all()


@router.get("/{id}", response_model=ActivityGet)
def get_by_id(id: int):
    return activity_service.get_by_id(id)


@router.put("/{id}")
def update(id: int, payload: ActivityUpdate, token: BaseToken = Depends(JWTBearer())):
    activity, updated = activity_service.update(id, payload, token)
    return {"success": True, "updated_id": activity.id, "updated": updated}


@router.post("/")
def create(payload: ActivityCreate, token: BaseToken = Depends(JWTBearer())):
    activity = activity_service.create(payload, token)
    return {"success": True, "created_id": activity.id}


@router.delete("/{id}")
def delete(id: int, token: BaseToken = Depends(JWTBearer())):
    activity = activity_service.delete(id, token)
    return {"success": True, "deleted_id": activity.id}
