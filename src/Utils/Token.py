from __future__ import annotations
import enum
from typing import List
import jwt
from dateutil import parser
from datetime import datetime, timedelta

from src.utils.Configuration import Configuration
from src.error.AuthenticationException import AuthenticationException
from src.utils.UserType import UserType
from src.impl.User.service import UserService

from src.impl.User.model import User as UserModel

SECRET_KEY = Configuration.get("SECURITY", "SECRET_KEY")
ALGORITHM = Configuration.get("SECURITY", "ALGORITHM")
SERVICE_TOKEN = Configuration.get("SECURITY", "SERVICE_TOKEN")
ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.get("SECURITY",
                                                "ACCESS_TOKEN_EXPIRE_MINUTES")


class TokenType(enum.Enum):
    ACCESS = 'access'
    REFRESH = 'refresh'
    ASSISTENCE = 'assistence'
    VERIFICATION = 'verification'
    RESET_PASS = 'reset_pass'


# TODO: fer que sigui abstracta
class BaseToken:
    user_id: int = 0
    expt: int = 0
    type: str = ''
    email: str = ''
    user_type: str = ''
    is_admin: bool = False

    user_service = UserService()

    def __init__(self, user: UserModel):
        self.expt = (
            datetime.utcnow() +
            timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))).isoformat()
        if user is None:
            return
        self.user_id = user.id
        self.email - user.email
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
        data = self.decode(token)
        self.user_id = data.get("user_id")
        self.expt = data.get("expt")
        self.type = data.get("type")
        self.email = data.get("email")
        return data

    def to_token(self):
        return BaseToken.encode(self.__dict__)

    def user_set(self, user: UserModel):
        if type == TokenType.ACCESS.value:
            user.token = self.to_token()
        elif type == TokenType.REFRESH.value:
            user.refresh_token = self.to_token()
        elif type == TokenType.RESET_PASS.value:
            user.rest_password_token = self.to_token()
        elif type == TokenType.VERIFICATION.value:
            user.verification_token = self.to_token()

    def check(self, available_users:List[UserType], user_id: int = None):
        types=[t.value for t in available_users]
        if self.user_type not in types and not self.user_type == UserType.SERVICE:
            return False
        if self.user_type in [UserType.HACKER.value, UserType.COMPANYUSER.value, UserType.LLEIDAHACKER.value]:
            if user_id is not None:
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
        return jwt.decode(token.encode('utf-8'),
                          SECRET_KEY,
                          algorithms=[ALGORITHM])

    # @classmethod
    def encode(dict):
        return jwt.encode(dict, SECRET_KEY, algorithm=ALGORITHM)

    # @classmethod
    def verify(token):
        if BaseToken.is_service(token):
            return True
        dict = BaseToken.decode(token)
        user = BaseToken.user_service.get_by_id(dict["user_id"])
        if user.type != dict["type"]:
            raise AuthenticationException("Invalid token")
        data = BaseToken.from_token(token)
        #TODO: comprovar tipus de token

        if user.token != token:
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
        self.type = TokenType.ASSISTENCE.value
        super().__init__(user)
        self.event_id = event_id

    def from_token(self, token):
        data = super().from_token(token)
        self.event_id = data.get("event_id")

    def verify(self, user: UserModel):
        return True


class AccesToken(BaseToken):
    is_verified: bool = False
    available: bool = True

    def __init__(self, user: UserModel):
        self.type = TokenType.ACCESS.value
        super().__init__(user)
        if user is None:
            return
        self.is_verified = user.is_verified
        if self.user_type == UserType.HACKER.value:
            self.available = not user.banned
        elif user.type == UserType.LLEIDAHACKER.value:
            self.available = user.active and user.accepted and not user.rejected
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
        self.type = TokenType.REFRESH.value
        super().__init__(user)


class VerificationToken(BaseToken):

    def __init__(self, user: UserModel):
        if user is None:
            return
        self.type = TokenType.VERIFICATION.value
        super().__init__(user)


class ResetPassToken(BaseToken):

    def __init__(self, user: UserModel):
        if user is None:
            return
        self.type = TokenType.RESET_PASS.value
        super().__init__(user)
