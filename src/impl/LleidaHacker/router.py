from typing import List, Union
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from src.utils.database import get_db
from src.utils.Token import AccesToken, BaseToken, RefreshToken, VerificationToken
from src.utils.JWTBearer import JWTBearer

from src.impl.LleidaHacker.schema import LleidaHackerGet as LleidaHackerGetSchema
from src.impl.LleidaHacker.schema import LleidaHackerGetAll as LleidaHackerGetAllSchema
from src.impl.LleidaHacker.schema import LleidaHackerCreate as LleidaHackerCreateSchema
from src.impl.LleidaHacker.schema import LleidaHackerUpdate as LleidaHackerUpdateSchema

from src.impl.LleidaHacker.service import LleidaHackerService
from services.mail import send_registration_confirmation_email

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
)

lleidahacker_service = LleidaHackerService()


@router.post("/signup")
def signup(payload: LleidaHackerCreateSchema, db: Session = Depends(get_db)):
    new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
    access_token = AccesToken(new_lleidahacker).save_to_user()
    refresh_token = RefreshToken(new_lleidahacker).save_to_user()
    VerificationToken(new_lleidahacker).save_to_user()
    send_registration_confirmation_email(new_lleidahacker)
    return {
        "success": True,
        "user_id": new_lleidahacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[LleidaHackerGetSchema])
def get_lleidahacker(str=Depends(JWTBearer())):
    return lleidahacker_service.get_all()


@router.get("/{userId}",
            response_model=Union[LleidaHackerGetAllSchema, LleidaHackerGetSchema])
def get_lleidahacker(userId: int, data: BaseToken = Depends(JWTBearer())):
    return lleidahacker_service.get_lleidahacker(userId, data)


# @router.post("/")
# def add_lleidahacker(payload: SchemaLleidaHacker,
#                            response: Response,
#                            str=Depends(JWTBearer())):
#     new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
#     return {"success": True, "user_id": new_lleidahacker.id}


@router.delete("/{userId}")
def delete_lleidahacker(userId: int, data: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.delete_lleidahacker(userId, data)
    return {"success": True, "deleted_id": userId}


@router.put("/{userId}")
def update_lleidahacker(userId: int,
                        payload: LleidaHackerUpdateSchema,
                        token: BaseToken = Depends(JWTBearer())):
    lleidahacker, updated = lleidahacker_service.update_lleidahacker(
        userId, payload, token)
    return {"success": True, "updated_id": userId, 'updated': updated}


@router.post("/{userId}/accept")
def accept_lleidahacker(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.accept_lleidahacker(
        userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/reject")
def reject_lleidahacker(userId: int, token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.reject_lleidahacker(
        userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/activate")
def activate_lleidahacker(userId: int,
                          token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.activate_lleidahacker(
        userId, token)
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/deactivate")
def deactivate_lleidahacker(userId: int,
                            token: BaseToken = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.deactivate_lleidahacker(
        userId, token)
    return {"success": True, "updated_id": userId}
