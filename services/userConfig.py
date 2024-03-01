from pydantic import parse_obj_as
from models.User import User
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







##Funcións per preparar la creació de userConfig de tots els usuaris i que vagi ben ordenat el valor de id
def delete_user_config(db: Session, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    
    db.execute('UPDATE "user" SET config_id = NULL')
    db.commit()
    db.query(ModelUserConfig).delete()
    db.commit()





def create_user_configs(db: Session, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    
    users = db.query(User).all()
    success_count = 0
    failed_count = 0
    user_configs = []
    for user in users:
        user_config = ModelUserConfig(user_id=user.id, defaultLang="ca-CA", comercialNotifications=True, reciveNotifications=True)
        user_configs.append(user_config)
    
    db.execute('ALTER SEQUENCE user_config_id_seq RESTART WITH 0')  # TODO: Arreglar esto para que al crear la tabla, empiece en 1 y no en 150 o por ahi
    db.bulk_save_objects(user_configs)
    db.commit()
    
    for user_config in user_configs:
        user = db.query(User).filter(User.id == user_config.user_id).first()
        if user:
            user.config_id = user_config.id
            success_count += 1
        else:
            failed_count += 1
    
    db.commit()
    
    return success_count, failed_count
