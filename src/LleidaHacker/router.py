from src.LleidaHacker.schema import LleidaHacker as SchemaLleidaHacker
from src.LleidaHacker.schema import LleidaHackerUpdate as SchemaLleidaHackerUpdate

from database import get_db
from security import create_all_tokens, get_data_from_token
from services.mail import send_registration_confirmation_email
from utils.auth_bearer import JWTBearer

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import src.LleidaHacker.service as lleidahacker_service

router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
)


@router.post("/signup")
def signup(payload: SchemaLleidaHacker,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
    access_token, refresh_token = create_all_tokens(new_lleidahacker, db)
    send_registration_confirmation_email(new_lleidahacker)
    return {
        "success": True,
        "user_id": new_lleidahacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all")
def get_lleidahacker(db: Session = Depends(get_db),
                           str=Depends(JWTBearer())):
    return lleidahacker_service.get_all(db)


@router.get("/{userId}")
def get_lleidahacker(userId: int,
                           response: Response,
                           db: Session = Depends(get_db),
                           str=Depends(JWTBearer())):
    return lleidahacker_service.get_lleidahacker(
        userId, db, get_data_from_token(str))


# @router.post("/")
# def add_lleidahacker(payload: SchemaLleidaHacker,
#                            response: Response,
#                            db: Session = Depends(get_db),
#                            str=Depends(JWTBearer())):
#     new_lleidahacker = lleidahacker_service.add_lleidahacker(payload, db)
#     return {"success": True, "user_id": new_lleidahacker.id}


@router.delete("/{userId}")
def delete_lleidahacker(userId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.delete_lleidahacker(
        userId, db, get_data_from_token(token))
    return {"success": True, "deleted_id": userId}


@router.put("/{userId}")
def update_lleidahacker(userId: int,
                              payload: SchemaLleidaHackerUpdate,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    lleidahacker, updated = lleidahacker_service.update_lleidahacker(
        userId, payload, db, get_data_from_token(token))
    return {"success": True, "updated_id": userId, 'updated': updated}


@router.post("/{userId}/accept")
def accept_lleidahacker(userId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.accept_lleidahacker(
        userId, db, get_data_from_token(token))
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/reject")
def reject_lleidahacker(userId: int,
                              response: Response,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.reject_lleidahacker(
        userId, db, get_data_from_token(token))
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/activate")
def activate_lleidahacker(userId: int,
                                response: Response,
                                db: Session = Depends(get_db),
                                token: str = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.activate_lleidahacker(
        userId, db, get_data_from_token(token))
    return {"success": True, "updated_id": userId}


@router.post("/{userId}/deactivate")
def deactivate_lleidahacker(userId: int,
                                  response: Response,
                                  db: Session = Depends(get_db),
                                  token: str = Depends(JWTBearer())):
    lleidahacker = lleidahacker_service.deactivate_lleidahacker(
        userId, db, get_data_from_token(token))
    return {"success": True, "updated_id": userId}
