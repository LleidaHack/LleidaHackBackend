from __future__ import annotations

from fastapi_sqlalchemy import db

# from src.utils.service_utils import check_image
from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException
from src.impl.User.model import User as ModelUser
from src.impl.User.schema import UserGet as UserGetSchema
from src.impl.User.schema import UserGetAll as UserGetAllSchema
from src.utils.Base.BaseService import BaseService
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
        db.session.refresh(user)

    def get_all(self):
        return db.session.query(ModelUser).all()

    def get_by_id(self, userId: int):
        user = db.session.query(ModelUser).filter(
            ModelUser.id == userId).first()
        if user is None:
            raise NotFoundException("User not found")
        return user

    def get_by_email(self, email: str, exc=True):
        user = db.session.query(ModelUser).filter(
            ModelUser.email == email).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_nickname(self, nickname: str, exc=True):
        user = db.session.query(ModelUser).filter(
            ModelUser.nickname == nickname).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_phone(self, phone: str, exc=True):
        user = db.session.query(ModelUser).filter(
            ModelUser.telephone == phone).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def get_by_code(self, code: str, exc=True):
        user = db.session.query(ModelUser).filter(
            ModelUser.code == code).first()
        if user is None and exc:
            raise NotFoundException("User not found")
        return user

    def count_users(self):
        return db.session.query(ModelUser).count()

    def get_user(self, userId: int, data):
        user = self.get_by_id(userId)
        if data.check([UserType.LLEIDAHACKER], userId):
            return UserGetAllSchema.from_orm(user)
        return UserGetSchema.from_orm(user)

    def get_user_by_email(self, email: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_email(email)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAllSchema.from_orm(user)
        return UserGetSchema.from_orm(user)

    def get_user_by_nickname(self, nickname: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_nickname(nickname)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAllSchema.from_orm(user)
        return UserGetSchema.from_orm(user)

    def get_user_by_phone(self, phone: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_phone(phone)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAllSchema.from_orm(user)
        return UserGetSchema.from_orm(user)

    def get_user_by_code(self, code: str, data):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.get_by_code(code)
        if data.check([UserType.LLEIDAHACKER], user.id):
            return UserGetAllSchema.from_orm(user)
        return UserGetSchema.from_orm(user)

    # def add_user(self, payload: SchemaUser):
    #     new_user = ModelUser(**payload.dict())
    #     if payload.image is not None:
    #         payload = check_image(payload)
    #     new_user.password = get_password_hash(payload.password)
    #     db.session.add(new_user)
    #     db.session.commit()
    #     return new_user

    # def delete_user(self, userId: int):
    #     return self.get_by_id(userId).delete()