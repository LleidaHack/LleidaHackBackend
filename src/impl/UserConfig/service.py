from fastapi_sqlalchemy import db

from src.error.AuthorizationException import AuthorizationException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User
from src.impl.UserConfig.model import UserConfig
from src.impl.UserConfig.schema import (
    UserConfigCreate,
    UserConfigGetAll,
    UserConfigUpdate,
)
from src.utils.Base.BaseService import BaseService
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class UserConfigService(BaseService):
    name = "user_config_service"

    def get_all(self):
        return db.session.query(UserConfig).all()

    def get_by_id(self, id: int):
        config = db.session.query(UserConfig).filter(UserConfig.id == id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_by_user_id(self, user_id: int):
        config = (
            db.session.query(UserConfig)
            .join(User, User.config_id == UserConfig.id)
            .filter(User.id == user_id)
            .first()
        )
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_user_config(self, userId: int, data: BaseToken):
        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], userId
        ):
            raise AuthorizationException("Not authorized")

        return UserConfigGetAll.model_validate(self.get_by_user_id(userId))

    def get_all_users_config(self, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthorizationException("Not authorized")

        return self.get_all()

    def add_user_config(self, payload: UserConfigCreate):
        userConfig = UserConfig(**payload.model_dump())
        db.session.add(userConfig)
        db.session.commit()
        return userConfig

    def update_user_config(
        self, user_id: int, payload: UserConfigUpdate, data: BaseToken
    ):
        if not data.check(
            [UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], user_id
        ):
            raise AuthorizationException("Not authorized")

        userConfig = self.get_by_user_id(user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(userConfig, field, value)
        db.session.commit()
        db.session.refresh(userConfig)
        return userConfig
