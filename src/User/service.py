from sqlalchemy.orm import Session
from security import get_password_hash

from src.User.model import User as ModelUser
from src.Utils.UserType import UserType
from src.Utils.TokenData import TokenData

from src.User.schema import UserGet as SchemaUser

from utils.service_utils import check_image
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException

from utils.hide_utils import user_show_private


def get_all(db: Session):
    return db.query(ModelUser).all()


def count_users(db: Session):
    return db.query(ModelUser).count()


def get_user(db: Session, userId: int, data: TokenData):
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    if user is None:
        raise NotFoundException("User not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value
                          or data.user_id == userId)):
        user_show_private(user)
    return user


def get_user_by_email(db: Session, email: str, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if user is None:
        raise NotFoundException("User not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value
                          or data.user_id == user.id)):
        user_show_private(user)
    return user


def get_user_by_nickname(db: Session, nickname: str, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.nickname == nickname).first()
    if user is None:
        raise NotFoundException("User not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value
                          or data.user_id == user.id)):
        user_show_private(user)
    return user


def get_user_by_phone(db: Session, phone: str, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.telephone == phone).first()
    if user is None:
        raise NotFoundException("User not found")
    if data.is_admin or (data.available and
                         (data.type == UserType.LLEIDAHACKER.value
                          or data.user_id == user.id)):
        user_show_private(user)
    return user


def get_user_by_code(db: Session, code: str, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    user = db.query(ModelUser).filter(ModelUser.code == code).first()
    if user is None:
        raise NotFoundException("User not found")
    return user


def add_user(db: Session, payload: SchemaUser):
    new_user = ModelUser(**payload.dict())
    if payload.image is not None:
        payload = check_image(payload)
    new_user.password = get_password_hash(payload.password)
    db.add(new_user)
    db.commit()
    return new_user


def delete_user(db: Session, userId: int):
    return db.query(ModelUser).filter(ModelUser.id == userId).delete()


def update_user(db: Session, userId: int, payload: SchemaUser):
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    user.name = payload.name
    user.password = payload.password
    user.nickname = payload.nickname
    user.birthdate = payload.birthdate
    user.food_restrictions = payload.food_restrictions
    user.telephone = payload.telephone
    user.address = payload.address
    user.shirt_size = payload.shirt_size
    user.image_id = payload.image_id
    db.commit()
    db.refresh(user)
    return user


def set_user_token(db: Session, userId: int, token: str,
                         refresh_token: str):
    user = db.query(ModelUser).filter(ModelUser.id == userId).first()
    user.token = token
    user.refresh_token = refresh_token
    db.commit()
    db.refresh(user)
    return user
