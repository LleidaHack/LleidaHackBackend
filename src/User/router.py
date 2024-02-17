from typing import List, Union
from fastapi import Depends, APIRouter
from pydantic import parse_obj_as
from sqlalchemy.orm import Session

from database import get_db
from security import get_data_from_token
from utils.auth_bearer import JWTBearer

import src.User.service as user_service

from src.User.schema import UserGet as UserGetSchema
from src.User.schema import UserGetAll as UserGetAllSchema
# from User.schema import UserCreate as UserCreateSchema
# from User.schema import UserCreate as UserCreateSchema

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.get("/count")
def count_users(db: Session = Depends(get_db),
                token: str = Depends(JWTBearer())):
    return user_service.count_users(db)


@router.get("/all", response_model=List[UserGetSchema])
def get_users(db: Session = Depends(get_db),
              token: str = Depends(JWTBearer())):
    return user_service.get_all(db)


@router.get(
    "/{userId}", response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user(userId: int,
             db: Session = Depends(get_db),
             str=Depends(JWTBearer())):
    return user_service.get_user(db, userId, get_data_from_token(str))


@router.get("/email/{email}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_email(email: str,
                      db: Session = Depends(get_db),
                      str=Depends(JWTBearer())):
    return user_service.get_user_by_email(db, email, get_data_from_token(str))


@router.get("/nickname/{nickname}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_nickname(nickname: str,
                         db: Session = Depends(get_db),
                         str=Depends(JWTBearer())):
    return user_service.get_user_by_nickname(db, nickname,
                                             get_data_from_token(str))


@router.get("/phone/{phone}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_phone(phone: str,
                      db: Session = Depends(get_db),
                      str=Depends(JWTBearer())):
    return user_service.get_user_by_phone(db, phone, get_data_from_token(str))


@router.get("/code/{code}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_code(code: str,
                     db: Session = Depends(get_db),
                     str=Depends(JWTBearer())):
    return user_service.get_user_by_code(db, code, get_data_from_token(str))


# @router.post("/")
# def add_user(payload: SchemaUser,
#                    db: Session = Depends(get_db),
#                    str=Depends(JWTBearer())):
#     new_user = user_service.add_user(db, payload)
#     return {"success": True, "user_id": new_user.id}

# @router.put("/{userId}")
# def update_user(userId: int,
#                       payload: SchemaUser,
#                       response: Response,
#                       db: Session = Depends(get_db),
#                       str=Depends(JWTBearer())):
#     return user_service.update_user(db, userId, payload)

# @router.delete("/{userId}")
# def delete_user(userId: int,
#                       response: Response,
#                       db: Session = Depends(get_db),
#                       str=Depends(JWTBearer())):
#     return user_service.delete_user(db, userId)
