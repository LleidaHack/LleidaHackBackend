from fastapi_sqlalchemy import db
from pydantic import TypeAdapter

from src.error.AuthenticationError import AuthenticationError
from src.error.NotFoundError import NotFoundError
from src.impl.User.model import User
from src.impl.UserConfig.model import UserConfig
from src.impl.UserConfig.schema import (
    UserConfigCreate,
    UserConfigGet,
    UserConfigGetAll,
    UserConfigUpdate,
)
from src.utils.Base.BaseService import BaseService
from src.utils.token import BaseToken
from src.utils.user_type import UserType


class UserConfigService(BaseService):
    name = 'user_config_service'

    def get_all(self):
        return db.session.query(UserConfig).all()

    def get_by_id(self, config_id: int):
        config = db.session.query(UserConfig).filter(UserConfig.id == config_id).first()
        if config is None:
            raise NotFoundError('User config not found')
        return config

    def get_by_user_id(self, user_id: int):
        config = (
            db.session.query(UserConfig).filter(UserConfig.user_id == user_id).first()
        )
        if config is None:
            raise NotFoundError('User config not found')
        return config

    def get_user_config(self, user_id: int, data: BaseToken):
        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], user_id
        ):
            raise AuthenticationError('Not authorized')

        user_config = self.get_by_user_id(user_id)
        if data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], user_id
        ):
            return TypeAdapter(UserConfigGetAll).validate_python(user_config)

        return TypeAdapter(UserConfigGet).validate_python(user_config)

    def get_all_users_config(self, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationError('Not authorized')

        return self.get_all()

    def add_user_config(self, payload: UserConfigCreate):
        user_config = UserConfig(**payload.model_dump())
        db.session.add(user_config)
        db.session.commit()
        return user_config

    def update_user_config(
        self, config_id: int, payload: UserConfigUpdate, data: BaseToken
    ):
        user_config = self.get_by_id(config_id)
        user_id = db.session.query(User).filter(User.config_id == config_id).first().id

        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], user_id
        ):
            raise AuthenticationError('Not authorized')

        user_config.recive_notifications = payload.recive_notifications
        user_config.default_lang = payload.default_lang
        user_config.comercial_notifications = payload.comercial_notifications
        db.session.commit()
        db.session.refresh(user_config)
        return user_config
