from __future__ import annotations

from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from hmac import compare_digest
from typing import List

import jwt
from dateutil import parser

from src.configuration.Settings import settings
from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User
from src.impl.User.service import UserService
from src.utils.TokenType import TokenType
from src.utils.UserType import UserType

SECRET_KEY = settings.security.secret_key
ALGORITHM = settings.security.algorithm
SERVICE_TOKEN = settings.security.service_token
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.expire_time


class BaseToken:
    user_id: int = 0
    expt: str = ""
    type: str = ""
    email: str = ""
    user_type: str = ""
    is_admin: bool = False
    available: bool = False
    user_service = UserService()

    def __init__(self, user: User):
        self.expt = (
            datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        ).isoformat()
        if user is not None:
            self.user_id = user.id
            self.user_type = user.type
            self.email = user.email
            self.available = self.is_available(user)

    @staticmethod
    def is_available(user: User):
        if user.is_deleted or not user.is_verified:
            return False
        if user.type == UserType.HACKER.value:
            return not user.banned
        if user.type == UserType.LLEIDAHACKER.value:
            return bool(user.active and user.accepted)
        if user.type == UserType.COMPANYUSER.value:
            return bool(user.active)
        return False

    def from_token(self, token: str):
        payload = self.decode(token)
        for field in ("user_id", "user_type", "email", "type", "expt", "event_id"):
            if field in payload:
                setattr(self, field, payload[field])
        self._encoded = token
        return self

    def to_token(self):
        if hasattr(self, "_encoded"):
            return self._encoded
        return self.encode({k: v for k, v in vars(self).items() if not k.startswith("_")})

    def user_set(self):
        self.user_service.update_token(self)
        return self.to_token()

    def check(self, available_users: List[UserType], user_id: int = None):
        if self.user_type == UserType.SERVICE.value:
            return self.is_admin and self.available
        if self.type != TokenType.ACCESS.value or not self.available:
            return False
        if self.user_type not in [role.value for role in available_users]:
            return False
        return (
            user_id is None
            or self.user_type == UserType.LLEIDAHACKER.value
            or self.user_id == user_id
        )

    @staticmethod
    def is_service(token):
        return isinstance(token, str) and compare_digest(token.encode(), SERVICE_TOKEN.encode())

    @staticmethod
    def decode(token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if type(payload.get("user_id")) is not int or payload["user_id"] <= 0:
                raise ValueError("Invalid user")
            if payload.get("type") not in {item.value for item in TokenType}:
                raise ValueError("Invalid purpose")
            expiry = parser.isoparse(payload["expt"])
            if expiry.tzinfo is None or expiry <= datetime.now(UTC):
                raise ValueError("Invalid expiration")
            return payload
        except (jwt.InvalidTokenError, AttributeError, TypeError, ValueError, KeyError, OverflowError):
            raise AuthenticationException("Invalid or expired token") from None

    @staticmethod
    def encode(payload):
        return jwt.encode(OrderedDict(sorted(payload.items())), SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify(token, expected_type=TokenType.ACCESS):
        BaseToken.get_data(token, expected_type=expected_type)
        return True

    @staticmethod
    def get_data(token: str, expected_type=TokenType.ACCESS, require_available=True, allow_service=True):
        if BaseToken.is_service(token):
            if not allow_service or expected_type != TokenType.ACCESS:
                raise AuthenticationException("Invalid token purpose")
            data = BaseToken(None)
            data.user_type = UserType.SERVICE.value
            data.is_admin = True
            data.available = True
            data.email = "service"
            return data

        payload = BaseToken.decode(token)
        if payload["type"] != expected_type.value:
            raise AuthenticationException("Invalid token purpose")
        try:
            user = BaseToken.user_service.get_by_id(payload["user_id"])
        except NotFoundException:
            raise AuthenticationException("Invalid token") from None
        if user.is_deleted or user.type != payload.get("user_type"):
            raise AuthenticationException("Invalid token")
        stored_fields = {
            TokenType.ACCESS: "token",
            TokenType.REFRESH: "refresh_token",
            TokenType.RESET_PASS: "rest_password_token",
            TokenType.VERIFICATION: "verification_token",
        }
        if expected_type in stored_fields:
            stored = getattr(user, stored_fields[expected_type]) or ""
            if not compare_digest(stored.encode(), token.encode()):
                raise AuthenticationException("Invalid token")
        else:
            from fastapi_sqlalchemy import db
            from src.impl.Event.model import HackerRegistration

            if type(payload.get("event_id")) is not int:
                raise AuthenticationException("Invalid event")
            registration = db.session.query(HackerRegistration).filter_by(
                user_id=user.id, event_id=payload["event_id"]
            ).first()
            if (registration is None or registration.confirmed_assistance
                    or registration.confirm_assistance_token != token):
                raise AuthenticationException("Invalid token")

        token_classes = {
            TokenType.ACCESS: AccesToken,
            TokenType.REFRESH: RefreshToken,
            TokenType.RESET_PASS: ResetPassToken,
            TokenType.VERIFICATION: VerificationToken,
            TokenType.ASSISTENCE: AssistenceToken,
        }
        data = token_classes[expected_type](None).from_token(token)
        data.available = BaseToken.is_available(user)
        data.email = user.email
        data.is_admin = False
        if require_available and not data.available:
            raise AuthenticationException("Account is not available")
        return data


class AssistenceToken(BaseToken):
    def __init__(self, user: User, event_id: int = None):
        super().__init__(user)
        self.expt = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        self.type = TokenType.ASSISTENCE.value
        self.event_id = event_id


class AccesToken(BaseToken):
    def __init__(self, user: User):
        super().__init__(user)
        self.type = TokenType.ACCESS.value
        self.is_verified = bool(user and user.is_verified)


class RefreshToken(BaseToken):
    def __init__(self, user: User):
        super().__init__(user)
        self.type = TokenType.REFRESH.value


class VerificationToken(BaseToken):
    def __init__(self, user: User):
        super().__init__(user)
        self.type = TokenType.VERIFICATION.value


class ResetPassToken(BaseToken):
    def __init__(self, user: User):
        super().__init__(user)
        self.type = TokenType.RESET_PASS.value
