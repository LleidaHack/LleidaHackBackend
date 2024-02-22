from pydantic import parse_obj_as
from sqlalchemy.orm import Session
from security import get_password_hash

from src.impl.User.model import User as ModelUser
from src.utils.UserType import UserType
from src.utils.TokenData import TokenData

from src.impl.User.schema import UserGet as UserGetSchema
from src.impl.User.schema import UserGetAll as UserGetAllSchema
from src.utils.Base.BaseService import BaseService
from utils.Token.model import BaseToken

from utils.service_utils import check_image
from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException


class UserService(BaseService):

    def get_all(self):
        return self.db.query(ModelUser).all()

    def count_users(self):
        return self.db.query(ModelUser).count()

    def get_user(self, userId: int, data: TokenData):
        user = self.db.query(ModelUser).filter(ModelUser.id == userId).first()
        if user is None:
            raise NotFoundException("User not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value
                              or data.user_id == userId)):
            return parse_obj_as(UserGetAllSchema, user)
        return parse_obj_as(UserGetSchema, user)

    def get_user_by_id(self, userId:int):
        user = self.db.query(ModelUser).filter(ModelUser.id == userId).first()
        if not user:
            raise NotFoundException("User not found")
        return user

    def get_user_by_email(self, email: str, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        user = self.db.query(ModelUser).filter(
            ModelUser.email == email).first()
        if user is None:
            raise NotFoundException("User not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value
                              or data.user_id == user.id)):
            return parse_obj_as(UserGetAllSchema, user)
        return parse_obj_as(UserGetSchema, user)

    def get_user_by_nickname(self, nickname: str, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        user = self.db.query(ModelUser).filter(
            ModelUser.nickname == nickname).first()
        if user is None:
            raise NotFoundException("User not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value
                              or data.user_id == user.id)):
            return parse_obj_as(UserGetAllSchema, user)
        return parse_obj_as(UserGetSchema, user)

    def get_user_by_phone(self, phone: str, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        user = self.db.query(ModelUser).filter(
            ModelUser.telephone == phone).first()
        if user is None:
            raise NotFoundException("User not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value
                              or data.user_id == user.id)):
            return parse_obj_as(UserGetAllSchema, user)
        return parse_obj_as(UserGetSchema, user)

    def get_user_by_code(self, code: str, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException("Not authorized")
        user = self.db.query(ModelUser).filter(ModelUser.code == code).first()
        if user is None:
            raise NotFoundException("User not found")
        if data.is_admin or (data.available and
                             (data.type == UserType.LLEIDAHACKER.value
                              or data.user_id == user.id)):
            return parse_obj_as(UserGetAllSchema, user)
        return parse_obj_as(UserGetSchema, user)

    # def add_user(self, payload: SchemaUser):
    #     new_user = ModelUser(**payload.dict())
    #     if payload.image is not None:
    #         payload = check_image(payload)
    #     new_user.password = get_password_hash(payload.password)
    #     self.db.add(new_user)
    #     self.db.commit()
    #     return new_user

    def delete_user(self, userId: int):
        return self.db.query(ModelUser).filter(ModelUser.id == userId).delete()

    # def update_user(self, userId: int, payload: UserUpdateSchema):
    #     user = self.db.query(ModelUser).filter(ModelUser.id == userId).first()
    #     user.name = payload.name
    #     user.password = payload.password
    #     user.nickname = payload.nickname
    #     user.birthdate = payload.birthdate
    #     user.food_restrictions = payload.food_restrictions
    #     user.telephone = payload.telephone
    #     user.address = payload.address
    #     user.shirt_size = payload.shirt_size
    #     user.image_id = payload.image_id
    #     self.db.commit()
    #     self.db.refresh(user)
    #     return user

    def set_user_token(self, userId: int, token: str, refresh_token: str):
        user = self.db.query(ModelUser).filter(ModelUser.id == userId).first()
        user.token = token
        user.refresh_token = refresh_token
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_token(self, token:BaseToken):
        user = self.get_user_by_id(token.user_id)
        token.user_set(user)
        self.db.commit()
        self.db.refresh(user)
        return 