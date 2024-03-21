from os import name
from pydantic import parse_obj_as
from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User
from src.impl.UserConfig.model import UserConfig as ModelUserConfig
from src.impl.UserConfig.schema import \
    UserConfigCreate as SchemaUserConfigCreate
from src.impl.UserConfig.schema import UserConfigGet as SchemaUserConfigGet
from src.impl.UserConfig.schema import \
    UserConfigGetAll as SchemaUserConfigGetAll
from src.impl.UserConfig.schema import \
    UserConfigUpdate as SchemaUserConfigUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class UserConfigService(BaseService):
    name = 'user_config_service'

    def get_all(self):
        return db.session.query(ModelUserConfig).all()

    def get_by_id(self, id: int):
        config = db.session.query(ModelUserConfig).filter(
            ModelUserConfig.id == id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_by_user_id(self, user_id: int):
        config = db.session.query(ModelUserConfig).filter(
            ModelUserConfig.user_id == user_id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_user_config(self, userId: int, data: BaseToken):
        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER],
                userId):
            raise AuthenticationException("Not authorized")

        userConfig = self.get_by_user_id(userId)
        if data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER],
                userId):
            return parse_obj_as(SchemaUserConfigGetAll, userConfig)

        return parse_obj_as(SchemaUserConfigGet, userConfig)

    def get_all_users_config(self, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")

        return self.get_all()

    def add_user_config(self, payload: SchemaUserConfigCreate):
        userConfig = ModelUserConfig(**payload.dict())
        db.session.add(userConfig)
        db.session.commit()
        return userConfig

    def update_user_config(self, config_id: int,
                           payload: SchemaUserConfigUpdate, data: BaseToken):
        userConfig = self.get_by_id(config_id)

        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER],
                userConfig.user_id):
            raise AuthenticationException("Not authorized")

        userConfig.reciveNotifications = payload.reciveNotifications
        userConfig.defaultLang = payload.defaultLang
        userConfig.comercialNotifications = payload.comercialNotifications
        db.session.commit()
        db.session.refresh(userConfig)
        return userConfig

    ##Funcións per preparar la creació de userConfig de tots els usuaris i que vagi ben ordenat el valor de id
    def delete_user_config(self, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")

        db.session.execute('UPDATE "{}" SET config_id = NULL'.format(
            User.__tablename__))
        db.session.commit()
        db.session.query(ModelUserConfig).delete()
        db.session.commit()

    def create_user_configs(self, data: BaseToken):
        
        if not data.is_admin:
            raise AuthenticationException("Not authorized")

        
        success_count = 0
        failed_count = 0
       
       
        user_config = ModelUserConfig(  defaultLang="ca-CA",
                                        comercialNotifications=True,
                                        reciveNotifications=True)
            
        users = db.session.query(User).all()
        for u in users:
            db.session.add(user_config)
            db.session.flush()
            if u:
                u.config_id = user_config.id
                success_count += 1
            else:
                failed_count += 1

        db.session.commit()
        return success_count, failed_count
