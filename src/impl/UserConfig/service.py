from os import name
from pydantic import TypeAdapter
from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User
from src.impl.UserConfig.model import UserConfig
from src.impl.UserConfig.schema import UserConfigCreate
from src.impl.UserConfig.schema import UserConfigGet
from src.impl.UserConfig.schema import UserConfigGetAll
from src.impl.UserConfig.schema import UserConfigUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class UserConfigService(BaseService):
    name = 'user_config_service'

    def get_all(self):
        return db.session.query(UserConfig).all()

    def get_by_id(self, id: int):
        config = db.session.query(UserConfig).filter(
            UserConfig.id == id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_by_user_id(self, user_id: int):
        config = db.session.query(UserConfig).filter(
            UserConfig.user_id == user_id).first()
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
            return TypeAdapter(UserConfigGetAll).validate_python(userConfig)

        return TypeAdapter(UserConfigGet).validate_python(userConfig)

    def get_all_users_config(self, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")

        return self.get_all()

    def add_user_config(self, payload: UserConfigCreate):
        userConfig = UserConfig(**payload.model_dump())
        db.session.add(userConfig)
        db.session.commit()
        return userConfig

    def update_user_config(self, config_id: int,
                           payload: UserConfigUpdate, data: BaseToken):
        userConfig = self.get_by_id(config_id)
        user_id = db.session.query(User).filter(
            User.config_id == config_id).first().id

        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER],
                user_id):
            raise AuthenticationException("Not authorized")

        userConfig.recive_notifications = payload.recive_notifications
        userConfig.default_lang = payload.default_lang
        userConfig.comercial_notifications = payload.comercial_notifications
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
        db.session.query(UserConfig).delete()
        db.session.commit()

    def create_user_configs(self, data: BaseToken):

        if not data.is_admin:
            raise AuthenticationException("Not authorized")

        success_count = 0
        failed_count = 0

        user_config = UserConfig(default_lang="ca-CA",
                                      comercial_notifications=True,
                                      recive_notifications=True,
                                      terms_and_conditions=True)

        users = db.session.query(User).order_by(User.id).all()
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
