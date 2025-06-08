from fastapi import APIRouter

from src.impl.UserConfig.schema import UserConfigGet, UserConfigGetAll, UserConfigUpdate
from src.impl.UserConfig.service import UserConfigService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/userConfig',
    tags=['UserConfig'],
)

user_config_service = UserConfigService()


@router.get('/all', response_model=list[UserConfigGetAll])
def get_all(token: BaseToken = jwt_dependency):
    return user_config_service.get_all_users_config(token)


@router.get('/{user_id}', response_model=UserConfigGetAll | UserConfigGet)
def get(user_id: int, token: BaseToken = jwt_dependency):
    return user_config_service.get_user_config(user_id, token)


@router.put('/{user_id}')
def update(user_id: int, payload: UserConfigUpdate, token: BaseToken = jwt_dependency):
    return user_config_service.update_user_config(user_id, payload, token)
