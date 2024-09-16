from __future__ import annotations

from fastapi_sqlalchemy import db

# from src.utils.service_utils import check_image
from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User
from src.impl.User.schema import UserGet
from src.impl.User.schema import UserGetAll
from src.utils.Base.BaseService import BaseService
# from src.utils.Token import AccesToken
from src.utils.TokenType import TokenType
from src.utils.UserType import UserType


class UserService(BaseService):
    name = 'user_service'

    def update_token(self, token):
        user = self.get_by_id(token.user_id)
        type = token.type
        if type == TokenType.ACCESS.value:
            user.token = token.to_token()
        elif type == TokenType.REFRESH.value:
            user.refresh_token = token.to_token()
        elif type == TokenType.RESET_PASS.value:
            user.rest_password_token = token.to_token()
        elif type == TokenType.VERIFICATION.value:
            user.verification_token = token.to_token()
        db.session.commit()
        db.session.flush(user)
        db.session.refresh(user)

    def get_all(self):
        return db.session.query(User).all()

    def get_by_id(self, userId: int):
        user = db.session.query(User).filter(User.id == userId).first()
        if user is None:
            raise NotFoundException("User not found")
        # db.session.refresh(user)
        return user

    def get_by_email(self, email: str, exc=True):
        user = db.session.query(User).filter(User.email == email).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_nickname(self, nickname: str, exc=True):
        user = db.session.query(User).filter(User.nickname == nickname).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_phone(self, phone: str, exc=True):
        user = db.session.query(User).filter(User.telephone == phone).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_code(self, code: str, exc=True):
        user = db.session.query(User).filter(User.code == code).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def count_users(self):
        return db.session.query(User).count()

    def get_user(self, userId: int, data):
        user = self.get_by_id(userId)
        if data.check([UserType.LLEIDAHACKER], userId):
            return UserGetAll.model_validate(user)
        return UserGet.model_validate(user)

    def get_user_by_email(self, email: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_email(email)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAll.model_validate(user)
        return UserGet.model_validate(user)

    def get_user_by_nickname(self, nickname: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_nickname(nickname)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAll.model_validate(user)
        return UserGet.model_validate(user)

    def get_user_by_phone(self, phone: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_phone(phone)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAll.model_validate(user)
        return UserGet.model_validate(user)

    def get_user_by_code(self, code: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_code(code)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAll.model_validate(user)
        return UserGet.model_validate(user)

    def _verify_user(self, user_id: int):
        user = self.get_by_id(user_id)
        if user.is_verified:
            raise InvalidDataException("User already verified")
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        db.session.flush(user)
        db.session.refresh(user)
        return user

    # def add_user(self, payload: SchemaUser):
    #     new_user = User(**payload.model_dump())
    #     if payload.image is not None:
    #         payload = check_image(payload)
    #     new_user.password = get_password_hash(payload.password)
    #     db.session.add(new_user)
    #     db.session.commit()
    #     return new_user

    # def delete_user(self, userId: int):
    #     return self.get_by_id(userId).delete()
