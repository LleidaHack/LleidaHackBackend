from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.UserConfig.schema import UserConfigGet as SchemaUserConfigGet
from src.impl.UserConfig.schema import \
    UserConfigGetAll as SchemaUserConfigGetAll
from src.impl.UserConfig.schema import \
    UserConfigUpdate as SchemaUserConfigUpdate
from src.impl.UserConfig.service import UserConfigService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/userConfig",
    tags=["UserConfig"],
)

userConfig_service = UserConfigService()


@router.get("/all", response_model=List[SchemaUserConfigGetAll])
def get_user_configs(token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.get_all_users_config(token)


@router.get("/{userId}",
            response_model=Union[SchemaUserConfigGetAll, SchemaUserConfigGet])
def get_user_config(userId: int, token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.get_user_config(userId, token)


@router.put("/{userId}")
def update_user_config(userId: int,
                       payload: SchemaUserConfigUpdate,
                       token: BaseToken = Depends(JWTBearer())):
    return userConfig_service.update_user_config(userId, payload, token)


##TODO: BORRAR DESPRES D'UTILITZAR
@router.delete("/")
def delete_user_config(token: BaseToken = Depends(JWTBearer())):
    userConfig_service.delete_user_config(token)

    return {"message": "UserConfig deleted successfully"}


@router.post("/")  ##TODO: FICAR NOM DESCRIPTIU /
def create_user_configs(token=Depends(JWTBearer())):
    return userConfig_service.create_user_configs(token)
