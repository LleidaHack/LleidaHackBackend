from sqlalchemy.orm import Session
from security import get_password_hash

from models.UserConfig import UserConfig as ModelUserConfig
from models.UserType import UserType
from models.TokenData import TokenData

from schemas.Userconfig import UserConfigCreate as SchemaUserConfig
from schemas.Userconfig import UserConfigUpdate as SchemaUserConfigUpdate


from utils.service_utils import check_image
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException

from utils.hide_utils import user_show_private





async def get_user_config(db: Session, userId: int, data: TokenData):
    userConfig = db.query(ModelUserConfig).filter(ModelUserConfig.user_id == userId).first()
    ##TODO: Comprobar si es ell mateix, lleidahacker o admin comprobar si esta available el usuari data.available
    #fer el parse object as parse_obj_as(el esquema a parsejar, el objecte)
    if userConfig is None:
        raise NotFoundException("User config not found")
    return userConfig

async def get_all_users_config(db: Session, userId: int, data: TokenData):
    userConfig = db.query(ModelUserConfig).all()
    ##TODO: comprobar si es Lleidahacker o admin 
    if len(userConfig) == 0 :
        raise NotFoundException("User config not found")
    return userConfig


async def add_user_config(db: Session, payload: SchemaUserConfig):
    userConfig = ModelUserConfig(**payload.dict())
    db.add(userConfig)
    db.commit()
    return userConfig



async def update_user_config(db: Session, userId: int, payload: SchemaUserConfigUpdate, data:TokenData):
    ##TODO: Comprobar si es ell mateix, lleidahacker o admin
    userConfig = db.query(ModelUserConfig).filter(ModelUserConfig.user_id == userId).first()
    userConfig.reciveNotifications = payload.reciveNotifications
    userConfig.defaultLang = payload.defaultLang
    userConfig.comercialNotifications = payload.comercialNotifications
    db.commit()
    db.refresh(userConfig)
    return userConfig


