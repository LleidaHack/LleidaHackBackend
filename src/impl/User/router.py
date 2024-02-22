from typing import List, Union
from fastapi import Depends, APIRouter

from security import get_data_from_token
from src.utils.Token.model import BaseToken
from utils.auth_bearer import JWTBearer

from src.impl.User.service import UserService

from src.impl.User.schema import UserGet as UserGetSchema
from src.impl.User.schema import UserGetAll as UserGetAllSchema

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

user_service = UserService()


@router.get("/count")
def count_users(token: BaseToken = Depends(JWTBearer())):
    return user_service.count_users()


@router.get("/all", response_model=List[UserGetSchema])
def get_users(token: BaseToken = Depends(JWTBearer())):
    return user_service.get_all()


@router.get("/{userId}", response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user(userId: int, str=Depends(JWTBearer())):
    return user_service.get_user(userId, get_data_from_token(str))


@router.get("/email/{email}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_email(email: str, str=Depends(JWTBearer())):
    return user_service.get_user_by_email(email, get_data_from_token(str))


@router.get("/nickname/{nickname}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_nickname(nickname: str, str=Depends(JWTBearer())):
    return user_service.get_user_by_nickname(nickname,
                                             get_data_from_token(str))


@router.get("/phone/{phone}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_phone(phone: str, str=Depends(JWTBearer())):
    return user_service.get_user_by_phone(phone, get_data_from_token(str))


@router.get("/code/{code}",
            response_model=Union[UserGetSchema, UserGetAllSchema])
def get_user_by_code(code: str, str=Depends(JWTBearer())):
    return user_service.get_user_by_code(code, get_data_from_token(str))


# @router.post("/")
# def add_user(payload: SchemaUser,
#
#                    str=Depends(JWTBearer())):
#     new_user = user_service.add_user(payload)
#     return {"success": True, "user_id": new_user.id}

# @router.put("/{userId}")
# def update_user(userId: int,
#                       payload: SchemaUser,
#                       response: Response,
#
#                       str=Depends(JWTBearer())):
#     return user_service.update_user(userId, payload)

# @router.delete("/{userId}")
# def delete_user(userId: int,
#                       response: Response,
#
#                       str=Depends(JWTBearer())):
#     return user_service.delete_user(userId)
