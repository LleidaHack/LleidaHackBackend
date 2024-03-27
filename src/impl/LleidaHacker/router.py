from typing import List, Union

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.mail import send_registration_confirmation_email
from src.impl.LleidaHacker.schema import \
    LleidaHackerCreate as LleidaHackerCreateSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerGet as LleidaHackerGetSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerGetAll as LleidaHackerGetAllSchema
from src.impl.LleidaHacker.schema import \
    LleidaHackerUpdate as LleidaHackerUpdateSchema
from src.impl.LleidaHacker.service import LleidaHackerService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import (AccesToken, BaseToken, RefreshToken,
                             VerificationToken)

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
)

lleidahacker_service = LleidaHackerService()


@router.post("/signup")
def signup(payload: LleidaHackerCreateSchema):
    new_lleidahacker = lleidahacker_service.add_lleidahacker(payload)
    access_token = AccesToken(new_lleidahacker).user_set()
    refresh_token = RefreshToken(new_lleidahacker).user_set()
    VerificationToken(new_lleidahacker).user_set()
    send_registration_confirmation_email(new_lleidahacker)
    return {
        "success": True,
        "user_id": new_lleidahacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[LleidaHackerGetSchema])
def get_all(str=Depends(JWTBearer())):
    return lleidahacker_service.get_all()


@router.get("/{userId}",
            response_model=Union[LleidaHackerGetAllSchema,
                                 LleidaHackerGetSchema])
def get(userId: int, data: BaseToken = Depends(JWTBearer())):
    return lleidahacker_service.get_lleidahacker(userId, data)


# @router.post("/")
# def add_lleidahacker(payload: SchemaLleidaHacker,
#                            response: Response,
#                            str=Depends(JWTBearer())):
#     new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
#     return {"success": True, "user_id": new_lleidahacker.id}


@router.delete("/{userId}")
def delete(userId: int, data: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.delete_lleidahacker(userId, data)
    return {"success": True, "deleted_id": userId}


@router.put("/{userId}")
def update(userId: int,
           payload: LleidaHackerUpdateSchema,
           token: BaseToken = Depends(JWTBearer())):
    lleidahacker, updated = lleidahacker_service.update_lleidahacker(
        userId, payload, token)
    return {"success": True, "updated_id": userId, 'updated': updated}


@router.post("/{userId}/accept")
def accept(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.accept_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/reject")
def reject(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.reject_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/activate")
def activate(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.activate_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/deactivate")
def deactivate(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.deactivate_lleidahacker(userId, token)
    return {"success": True, "updated_id": userId}
