import enum
import jwt
from dateutil import parser
from datetime import datetime, timedelta

from config import Configuration
from error.AuthenticationException import AuthenticationException
from utils.UserType import UserType
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


class BaseToken:
    user_id: int
    expt: int
    type: str
    email: str
    user_type: str
    is_admin: bool = False
    is_service: bool = False
    data = None

    user_service = UserService()

    def __init__(self, user: UserModel):
        self.user_id = user.id
        self.email - user.email
        # self.type =
        self.expt = (
            datetime.utcnow() +
            timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))).isoformat()
        self.user_type = user.type

    def from_token(self, token: str):
        if BaseToken.is_service(token):
            self.is_admin = True
            self.is_service = True
            self.user_id = 0
            self.available = True
            self.type = "service"
            self.email = ""
            return self
        self.data = self.decode(token)
        self.user_id = self.data.get("user_id")
        self.expt = self.data.get("expt")
        self.type = self.data.get("type")
        self.email = self.data.get("email")

    def to_token(self) -> str:
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

    def save_to_user(self):
        BaseToken.user_service.set_token(self)

    @classmethod
    def is_service(token):
        return token == SERVICE_TOKEN

    @classmethod
    def decode(token):
        return jwt.decode(token.encode('utf-8'),
                          SECRET_KEY,
                          algorithms=[ALGORITHM])

    @classmethod
    def encode(dict):
        return jwt.encode(dict, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def verify(token):
        if BaseToken.is_service(token):
            return True
        dict = BaseToken.decode(token)
        user = BaseToken.user_service.get_user_by_id(dict["user_id"])
        if user.type != dict["type"]:
            raise AuthenticationException("Invalid token")
        if user.token != token:
            raise AuthenticationException("Invalid token")
        # Here your code for verifying the token or whatever you use
        if parser.parse(dict["expt"]) < datetime.utcnow():
            raise AuthenticationException(message="Token expired")
        return True

    @classmethod
    def get_data(token: str):
        type = BaseToken.decode(token).get('type')
        if type == TokenType.ACCESS.value:
            return AccesToken(token)
        elif type == TokenType.ASSISTENCE.value:
            return AssistenceToken(token)
        elif type == TokenType.REFRESH.value:
            return RefreshToken(token)
        elif type == TokenType.RESET_PASS.value:
            return ResetPassToken(token)
        elif type == TokenType.VERIFICATION.value:
            return VerificationToken(token)


class AssistenceToken(BaseToken):
    event_id: int = 0

    def __init__(self, user: UserModel, event_id: int):
        self.type = TokenType.ASSISTENCE.value
        super().__init__(user)
        self.event_id = event_id

    def from_token(self, token):
        super().from_token(token)
        self.event_id = self.data.get("event_id")


class AccesToken(BaseToken):
    is_verified: bool = False
    available: bool = True

    def __init__(self, user: UserModel):
        self.type = TokenType.ACCESS.value
        super().__init__(user)
        self.is_verified = user.is_verified
        if self.user_type == UserType.HACKER.value:
            self.available = not user.banned
        elif user.type == UserType.LLEIDAHACKER.value:
            self.available = user.active and user.accepted and not user.rejected
        else:
            self.available = user.active

    def from_token(self, token):
        super().from_token(token)
        self.is_verified = self.data.get("is_verified")
        self.available = self.data.get("available")


class RefreshToken(BaseToken):

    def __init__(self, user: UserModel):
        self.type = TokenType.REFRESH.value
        super().__init__(user)


class VerificationToken(BaseToken):

    def __init__(self, user: UserModel):
        self.type = TokenType.VERIFICATION.value
        super().__init__(user)


class ResetPassToken(BaseToken):

    def __init__(self, user: UserModel):
        self.type = TokenType.RESET_PASS.value
        super().__init__(user)
