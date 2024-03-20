from pydantic import parse_obj_as

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
    def __call__(self):
        pass

    def get_all(self):
        return self.db.query(ModelUserConfig).all()

    def get_by_id(self, id: int):
        config = self.db.query(ModelUserConfig).filter(ModelUserConfig.id == id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config
    
    def get_by_user_id(self, user_id: int):
        config = self.db.query(ModelUserConfig).filter(ModelUserConfig.user_id == user_id).first()
        if config is None:
            raise NotFoundException("User config not found")
        return config

    def get_user_config(self, userId: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], userId):
            raise AuthenticationException("Not authorized")
        
        userConfig = self.get_by_user_id(userId)
        if data.check([UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], userId):
            return parse_obj_as(SchemaUserConfigGetAll, userConfig)

        return parse_obj_as(SchemaUserConfigGet, userConfig)


    def get_all_users_config(self, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        
        return self.get_all()


    def add_user_config(self, payload: SchemaUserConfigCreate):
        userConfig = ModelUserConfig(**payload.dict())
        self.db.add(userConfig)
        self.db.commit()
        return userConfig


    def update_user_config(self, config_id: int,
                        payload: SchemaUserConfigUpdate, data: BaseToken):
        userConfig = self.get_by_id(config_id)

        if not data.check([UserType.LLEIDAHACKER, UserType.HACKER, UserType.COMPANYUSER], userConfig.user_id):
            raise AuthenticationException("Not authorized")

        userConfig.reciveNotifications = payload.reciveNotifications
        userConfig.defaultLang = payload.defaultLang
        userConfig.comercialNotifications = payload.comercialNotifications
        self.db.commit()
        self.db.refresh(userConfig)
        return userConfig


    ##Funcións per preparar la creació de userConfig de tots els usuaris i que vagi ben ordenat el valor de id
    def delete_user_config(self, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")

        self.db.execute('UPDATE "user" SET config_id = NULL')
        self.db.commit()
        self.db.query(ModelUserConfig).delete()
        self.db.commit()


    def create_user_configs(self, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException("Not authorized")

        users = self.db.query(User).all()
        success_count = 0
        failed_count = 0
        user_configs = []
        for user in users:
            user_config = ModelUserConfig(user_id=user.id,
                                        defaultLang="ca-CA",
                                        comercialNotifications=True,
                                        reciveNotifications=True)
            user_configs.append(user_config)

        self.db.bulk_save_objects(user_configs)
        self.db.commit()

        for user_config in user_configs:
            user = self.db.query(User).filter(User.id == user_config.user_id).first()
            if user:
                user.config_id = user_config.id
                success_count += 1
            else:
                failed_count += 1

        self.db.commit()

        return success_count, failed_count
