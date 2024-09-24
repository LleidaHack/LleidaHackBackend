from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.UserConfig.schema import UserConfigGet
from src.impl.UserConfig.schema import UserConfigGetAll
from src.impl.UserConfig.schema import UserConfigUpdate
from src.impl.UserConfig.service import UserConfigService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/userConfig",
    tags=["UserConfig"],
)

userConfig_service = UserConfigService()


@router.get("/all", response_model=List[UserConfigGetAll])
def get_all(token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.get_all_users_config(token)


@router.get("/{userId}", response_model=Union[UserConfigGetAll, UserConfigGet])
def get(userId: int, token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.get_user_config(userId, token)


@router.put("/{userId}")
def update(userId: int,
           payload: UserConfigUpdate,
           token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.update_user_config(userId, payload, token)


##TODO: BORRAR DESPRES D'UTILITZAR
@router.delete("/")
def delete_all(token: BaseToken = Depends(JWTBearer())):
    userConfig_service.delete_user_config(token)

    return {"message": "UserConfig deleted successfully"}


@router.post("/userconfig_all_creator")
def create_all(token=Depends(JWTBearer())):
    return userConfig_service.create_user_configs(token)
