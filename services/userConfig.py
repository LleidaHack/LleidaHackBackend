from pydantic import parse_obj_as
from sqlalchemy.orm import Session
from security import get_data_from_token, get_password_hash

from models.UserConfig import UserConfig as ModelUserConfig
from models.UserType import UserType
from models.TokenData import TokenData

from schemas.Userconfig import UserConfigCreate as SchemaUserConfig, UserConfigGet, UserConfigGetAll
from schemas.Userconfig import UserConfigUpdate as SchemaUserConfigUpdate


from utils.service_utils import check_image
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException

from utils.hide_utils import user_show_private





def get_user_config(db: Session, userId: int, token: TokenData):
    data = get_data_from_token(token)
    userConfig = db.query(ModelUserConfig).filter(ModelUserConfig.user_id == userId).first()
    if userConfig is None:
        raise NotFoundException("User config not found")

    if data.is_admin or (data.available and(data.type == UserType.LLEIDAHACKER.value or data.user_id == userId)):
        return parse_obj_as(UserConfigGetAll, userConfig)
    return parse_obj_as(UserConfigGet, userConfig)
        

def get_all_users_config(db: Session, token: TokenData):
    data = get_data_from_token(token)
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    userConfig = db.query(ModelUserConfig).all()
    return userConfig


def add_user_config(db: Session, payload: SchemaUserConfig):
    userConfig = ModelUserConfig(**payload.dict())
    db.add(userConfig)
    db.commit()
    return userConfig


def update_user_config(db: Session, userId: int, payload: SchemaUserConfigUpdate, data:TokenData):
    userConfig = db.query(ModelUserConfig).filter(ModelUserConfig.user_id == userId).first()
    if userConfig is None:
            raise NotFoundException("User not found")
    
    if data.is_admin or (data.available and (data.type == UserType.LLEIDAHACKER.value or data.user_id == userId)):
        userConfig.reciveNotifications = payload.reciveNotifications
        userConfig.defaultLang = payload.defaultLang
        userConfig.comercialNotifications = payload.comercialNotifications
        db.commit()
        db.refresh(userConfig)
        return userConfig
    else:
        raise AuthenticationException("Not authorized")

