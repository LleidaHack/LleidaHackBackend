from fastapi import APIRouter

from src.impl.User.schema import UserGet, UserGetAll
from src.impl.User.service import UserService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/user',
    tags=['User'],
)

user_service = UserService()


@router.get('/count')
def count(token=jwt_dependency):
    # return BaseToken.get_data(token)
    return user_service.count_users()


@router.get('/all', response_model=list[UserGet])
def get_all(token: BaseToken = jwt_dependency):
    return user_service.get_all()


@router.get('/{user_id}', response_model=UserGetAll | UserGet)
def get(user_id: int, token: BaseToken = jwt_dependency):
    return user_service.get_user(user_id, token)


@router.get('/email/{email}', response_model=UserGetAll | UserGet)
def get_by_email(email: str, token: BaseToken = jwt_dependency):
    return user_service.get_user_by_email(email, token)


@router.get('/nickname/{nickname}', response_model=UserGetAll | UserGet)
def get_by_nickname(nickname: str, token: BaseToken = jwt_dependency):
    return user_service.get_user_by_nickname(nickname, token)


@router.get('/phone/{phone}', response_model=UserGetAll | UserGet)
def get_by_phone(phone: str, token: BaseToken = jwt_dependency):
    return user_service.get_user_by_phone(phone, token)


@router.get('/code/{code}', response_model=UserGetAll | UserGet)
def get_by_code(code: str, token: BaseToken = jwt_dependency):
    return user_service.get_user_by_code(code, token)
