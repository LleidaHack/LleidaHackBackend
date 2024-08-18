from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.User.schema import UserGet
from src.impl.User.schema import UserGetAll
from src.impl.User.service import UserService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

user_service = UserService()


@router.get("/count")
def count(token=Depends(JWTBearer())):
    # return BaseToken.get_data(token)
    return user_service.count_users()


@router.get("/all", response_model=List[UserGet])
def get_all(token: BaseToken = Depends(JWTBearer())):
    return user_service.get_all()


@router.get("/{userId}", response_model=Union[UserGetAll, UserGet])
def get(userId: int, token: BaseToken = Depends(JWTBearer())):
    return user_service.get_user(userId, token)


@router.get("/email/{email}",
            response_model=Union[UserGetAll, UserGet])
def get_by_email(email: str, token: BaseToken = Depends(JWTBearer())):
    return user_service.get_user_by_email(email, token)


@router.get("/nickname/{nickname}",
            response_model=Union[UserGetAll, UserGet])
def get_by_nickname(nickname: str, token: BaseToken = Depends(JWTBearer())):
    return user_service.get_user_by_nickname(nickname, token)


@router.get("/phone/{phone}",
            response_model=Union[UserGetAll, UserGet])
def get_by_phone(phone: str, token: BaseToken = Depends(JWTBearer())):
    return user_service.get_user_by_phone(phone, token)


@router.get("/code/{code}",
            response_model=Union[UserGetAll, UserGet])
def get_by_code(code: str, token: BaseToken = Depends(JWTBearer())):
    return user_service.get_user_by_code(code, token)
