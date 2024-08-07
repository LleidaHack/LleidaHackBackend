from __future__ import annotations
from collections import OrderedDict

from datetime import datetime, timedelta
from inspect import getfullargspec
from typing import List, overload

import jwt
from dateutil import parser

from src.configuration.Configuration import Configuration
from src.error.AuthenticationException import AuthenticationException
from src.impl.User.model import User as UserModel
from src.impl.User.service import UserService
from src.utils.TokenType import TokenType
from src.utils.UserType import UserType

SECRET_KEY = Configuration.security.secret_key
ALGORITHM = Configuration.security.algorithm
SERVICE_TOKEN = Configuration.security.service_token
ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.security.expire_time


# TODO: fer que sigui abstracta
class BaseToken:
    user_id: int = 0
    expt: int = 0
    type: str = ''
    email: str = ''
    user_type: str = ''
    is_admin: bool = False
    available: bool = True
    user_service = UserService()

    # def check_token(available_users: List[UserType], user_id: int = None):
    #     def wrapper(f):
    #         argspec = getfullargspec(f)
    #         argument_index = argspec.args.index('data')
    #         def c_t(*args):
    #             token = args[argument_index]
    #             if not isinstance(token, BaseToken):
    #                 raise Exception("This function has not token or its name is not data")
    #             types = [t.value for t in available_users]
    #             if (token.user_type not in types) and (not token.is_service):
    #                 return False
    #             if token.user_type in [
    #                     UserType.HACKER.value, UserType.COMPANYUSER.value,
    #                     UserType.LLEIDAHACKER.value
    #             ]:
    #                 if user_id is not None and token.user_type is not UserType.LLEIDAHACKER.value:
    #                     return token.available and token.user_id == user_id
    #                 return token.available
    #             elif token.user_type == UserType.SERVICE.value:
    #                 return token.is_admin
    #             else:
    #                 return False
    #         return c_t
    #     return wrapper
    # def __init__(self) -> None:
    #     return self.__init__(None)
    # @overload
    def __init__(self, user: UserModel):
        self.expt = (
            datetime.utcnow() +
            timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))).isoformat()
        if user is None:
            return
        self.user_id = user.id
        self.email = user.email
        # self.type =
        self.user_type = user.type

    def from_token(self, token: str):
        if BaseToken.is_service(token):
            self.is_admin = True
            # self.is_service = True
            self.user_id = 0
            self.available = True
            self.user_type = UserType.SERVICE.value
            self.email = "service"
            return self.__dict__
        data = BaseToken.decode(token)
        self.user_type = data.get("user_type")
        self.user_id = data.get("user_id")
        self.expt = data.get("expt")
        self.type = data.get("type")
        self.email = data.get("email")
        return self

    def to_token(self):
        return BaseToken.encode(self.__dict__)

    def user_set(self):
        self.user_service.update_token(self)
        return self.to_token()

    def check(self, available_users: List[UserType], user_id: int = None):
        types = [t.value for t in available_users]
        if (self.user_type not in types) and (not self.is_service):
            return False
        if self.user_type in [
                UserType.HACKER.value, UserType.COMPANYUSER.value,
                UserType.LLEIDAHACKER.value
        ]:
            if user_id is not None and self.user_type is not UserType.LLEIDAHACKER.value:
                return self.available and self.user_id == user_id
            return self.available
        elif self.user_type == UserType.SERVICE.value:
            return self.is_admin
        else:
            return False

    # data.check([UserType.LLEIDAHACKER, UserType.HACKER] , False, user_id)
    # data.check(['is_admin=False',
    #             'user_type in [LLEIDAHACKER,HACKER]',
    #             'user_id = '+ user_id])
    # def check(self, available_users:List[UserType], is_admin: bool, user_id: int = None):
    #     types=[t.value for t in available_users]
    #     if self.user_type not in types:
    #         return False
    #     ret = False
    #     if is_admin:
    #         ret = self.is_admin
    #     if user_id is not None:
    #         ret = ret and user_id == self.user_id

    # @classmethod
    def is_service(token):
        return token == SERVICE_TOKEN

    # @classmethod
    def decode(token):
        try:
            return jwt.decode(token.encode('utf-8'),
                              SECRET_KEY,
                              algorithms=[ALGORITHM])
        except Exception as e:
            raise Exception(f'Error decoding token with the token({token})')

    # @classmethod
    def encode(dict):
        return jwt.encode(OrderedDict(sorted(dict.items())), SECRET_KEY, algorithm=ALGORITHM)

    def verify(token):
        if BaseToken.is_service(token):
            return True
        dict = BaseToken.decode(token)
        user = BaseToken.user_service.get_by_id(dict["user_id"])
        if user.type != dict["user_type"]:
            raise AuthenticationException("Invalid token")
        data = BaseToken(None).from_token(token)
        #TODO: comprovar tipus de token

        if dict['type'] == TokenType.ACCESS and user.token != token:
            raise AuthenticationException("Invalid token")
        # Here your code for verifying the token or whatever you use
        if parser.parse(dict["expt"]) < datetime.utcnow():
            raise AuthenticationException("Token expired")
        return True

    # @classmethod
    def get_data(token: str):
        type = TokenType.ACCESS.value
        if not BaseToken.is_service(token):
            type = BaseToken.decode(token).get('type')
        if type == TokenType.ACCESS.value:
            return AccesToken(None).from_token(token)
        elif type == TokenType.ASSISTENCE.value:
            return AssistenceToken(None).from_token(token)
        elif type == TokenType.REFRESH.value:
            return RefreshToken(None).from_token(token)
        elif type == TokenType.RESET_PASS.value:
            return ResetPassToken(None).from_token(token)
        elif type == TokenType.VERIFICATION.value:
            return VerificationToken(None).from_token(token)


class AssistenceToken(BaseToken):
    event_id: int = 0

    def __init__(self, user: UserModel, event_id: int):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.ASSISTENCE.value
        self.event_id = event_id

    def from_token(self, token):
        data = super().from_token(token)
        self.event_id = data.get("event_id")
        return self

    def verify(self, user: UserModel):
        return True


class AccesToken(BaseToken):
    is_verified: bool = False
    available: bool = True

    def __init__(self, user: UserModel):
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

    def from_token(self, token):
        data = super().from_token(token)
        if not self.is_admin:
            self.is_verified = data.get("is_verified")
            self.available = data.get("available")
        return self

    def verify(self, user):
        return self.to_token() == user.token


class RefreshToken(BaseToken):

    def __init__(self, user: UserModel):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.REFRESH.value


class VerificationToken(BaseToken):

    def __init__(self, user: UserModel):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.VERIFICATION.value


class ResetPassToken(BaseToken):

    def __init__(self, user: UserModel):
        if user is None:
            return
        super().__init__(user)
        self.type = TokenType.RESET_PASS.value
