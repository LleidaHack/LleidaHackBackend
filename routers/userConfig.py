from typing import List, Union
from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import get_data_from_token
import services.userConfig as userConfig_service
from utils.auth_bearer import JWTBearer
from schemas.Userconfig import UserConfigGet as UserConfigGetSchema
from schemas.Userconfig import UserConfigGetAll as UserConfigGetAllSchema


from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/userConfig",
    tags=["UserConfig"],
)

@router.get("/all", response_model = List[UserConfigGetSchema])
async def get_user_configs(db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return await userConfig_service.get_all_users_config(db)


@router.get("/{userId}", response_model = Union[UserConfigGetSchema, UserConfigGetAllSchema]  )
async def get_user_config(userId: int,
                   db: Session = Depends(get_db),
                   token=Depends(JWTBearer())):
    return await userConfig_service.get_user_config(db, userId, get_data_from_token(token))


@router.put("/{userId}")
async def update_user_config(userId: int,
                       payload: SchemaUser,
                       db: Session = Depends(get_db),
                       token=Depends(JWTBearer())):
     return await userConfig_service.update_user_config(db, userId, payload, get_data_from_token(token))