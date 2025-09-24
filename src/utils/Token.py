from __future__ import annotations
from collections import OrderedDict

from datetime import datetime, timedelta, UTC
import token
from typing import List

import jwt
from dateutil import parser

from src.configuration.Settings import settings
from src.error.AuthenticationException import AuthenticationException
from src.impl.User.model import User
from src.impl.User.service import UserService
from src.utils.TokenType import TokenType
from src.utils.UserType import UserType

SECRET_KEY = settings.security.secret_key
ALGORITHM = settings.security.algorithm
SERVICE_TOKEN = settings.security.service_token
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.expire_time


# TODO: fer que sigui abstracta
class BaseToken:
    user_id: int = 0
    expt: int = 0
    type: str = ""
    email: str = ""
    user_type: str = ""
    is_admin: bool = False
    available: bool = True

    user_service = UserService()

    # def __set_all_data(self, data_in: dict):
    #     for _ in [
    #         _
    #         for _ in dir(self)
    #         if _.startswith("__") is False and _.endswith("__") is False
    #     ]:
    #         if _ in dir(data_in):
    #             setattr(self, _, getattr(data_in[_], _))
    
    def __set_all_data(self, data_in: dict):
        key_to_attribute_map = {
            'type': 'user_type'
        }

        for key, value in data_in.items():
            attribute_name = key_to_attribute_map.get(key, key)
            if hasattr(self, attribute_name):
                setattr(self, attribute_name, value)

    def __init__(self, user: User):
        self.expt = (
            datetime.now(UTC) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        ).isoformat()
        if user is None:
            return
        user_dict = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        self.__set_all_data(user_dict)
        self.user_type = user.type
        self.email = user.email

    def from_token(self, token: str):
        if BaseToken.is_service(token):
            return self.__get_service()
        data = BaseToken.decode(token)
        for _ in [
            _
            for _ in dir(self)
            if _.startswith("__") is False and _.endswith("__") is False
        ]:
            if _ in data:
                setattr(self, _, data[_])
        return self

    def __get_service(self):
        self.is_admin = True
        self.user_id = 0
        self.available = True
        self.user_type = UserType.SERVICE.value
        self.email = "service"
        return self.__dict__

    def to_token(self):
        return BaseToken.encode(self.__dict__)

    def user_set(self):
        self.user_service.update_token(self)
        return self.to_token()

    def check(self, available_users: List[UserType], user_id: int = None):
        types = [t.value for t in available_users]
        if (self.user_type not in types) and (not self.is_admin):
            return False
        if self.user_type in [
            UserType.HACKER.value,
            UserType.COMPANYUSER.value,
            UserType.LLEIDAHACKER.value,
        ]:
            if (
                user_id is not None
                and self.user_type is not UserType.LLEIDAHACKER.value
            ):
                return self.available and self.user_id == user_id
            return self.available
        elif self.user_type == UserType.SERVICE.value:
            return self.is_admin
        else:
            return False

    # @classmethod
    def is_service(token):
        return token == SERVICE_TOKEN

    # @classmethod
    def decode(token):
        try:
            return jwt.decode(token.encode("utf-8"), SECRET_KEY, algorithms=[ALGORITHM])
        except Exception:
            raise Exception(f"Error decoding token with the token({token})")

    # @classmethod
    def encode(dict):
        return jwt.encode(
            OrderedDict(sorted(dict.items())), SECRET_KEY, algorithm=ALGORITHM
        )

    def verify(token):
        if BaseToken.is_service(token):
            return True
        dict = BaseToken.decode(token)
        user = BaseToken.user_service.get_by_id(dict["user_id"])
        if user.type != dict["user_type"]:
            raise AuthenticationException("Invalid token")
        BaseToken(None).from_token(token)
        # TODO: comprovar tipus de token

        if dict["type"] == TokenType.ACCESS and user.token != token:
            raise AuthenticationException("Invalid token")
        # Here your code for verifying the token or whatever you use
        if parser.parse(dict["expt"]) < datetime.now(UTC):
            raise AuthenticationException("Token expired")
        return True

    # @classmethod
    def get_data(token: str):
        type = TokenType.ACCESS.value
        if not BaseToken.is_service(token):
            type = BaseToken.decode(token).get("type")
        if type == TokenType.ACCESS.value:
            return AccesToken(None).from_token(token)
        elif type == TokenType.ASSISTENCE.value:
            return AssistenceToken(None, None).from_token(token)
        elif type == TokenType.REFRESH.value:
            return RefreshToken(None).from_token(token)
        elif type == TokenType.RESET_PASS.value:
            return ResetPassToken(None).from_token(token)
        elif type == TokenType.VERIFICATION.value:
            return VerificationToken(None).from_token(token)


class AssistenceToken(BaseToken):
    event_id: int = 0

    def __init__(self, user: User, event_id: int):
        if user is None or event_id is None:
            return
        super().__init__(user)
        self.expt = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        self.type = TokenType.ASSISTENCE.value
        self.event_id = event_id

    def verify(self, user: User):
        return True


class AccesToken(BaseToken):
    is_verified: bool = False
    available: bool = True

    def __init__(self, user: User):
        super().__init__(user)
        self.type = TokenType.ACCESS.value
        if user is None:
            return
        self.is_verified = user.is_verified
        if self.user_type == UserType.HACKER.value:
            self.available = not bool(user.banned) and self.is_verified
        elif user.type == UserType.LLEIDAHACKER.value:
            self.available = user.active and user.accepted
        else:
            self.available = user.active

    # def from_token(self, token):
    #     data = super().from_token(token)
    #     if not self.is_admin:
    #         self.is_verified = data.get("is_verified")
    #         self.available = data.get("available")
    #     return self
    
    def from_token(self, token):
        payload = BaseToken.decode(token)  # dict real
        super().from_token(token)          # llena los atributos
        if not self.is_admin:
            self.is_verified = payload.get("is_verified")
            self.available  = payload.get("available")
        return self

    def verify(self, user):
        return self.to_token() == user.token


class RefreshToken(BaseToken):
    def __init__(self, user: User):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.REFRESH.value

    def from_token(self, token):
        super().from_token(token)
        return self


class VerificationToken(BaseToken):
    def __init__(self, user: User):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.VERIFICATION.value

    def from_token(self, token):
        super().from_token(token)
        return self


class ResetPassToken(BaseToken):
    def __init__(self, user: User):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.RESET_PASS.value

    def from_token(self, token):
        super().from_token(token)
        return self
