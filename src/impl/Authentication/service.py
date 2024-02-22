from datetime import datetime
from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from security import create_all_tokens, get_data_from_token, get_password_hash, verify_password
from src.utils.TokenData import TokenData
from src.utils.UserType import UserType

from src.error.InputException import InputException
from src.error.InvalidDataException import InvalidDataException
from src.error.AuthenticationException import AuthenticationException

from src.impl.User.model import User as ModelUser
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.LleidaHacker.model import LleidaHacker as ModelLleidaHacker
from src.impl.CompanyUser.model import CompanyUser as ModelCompanyUser

from services.mail import send_registration_confirmation_email, send_password_reset_email, send_contact_email
from src.utils.Token.model import AccesToken, RefreshToken, ResetPassToken

def create_access_and_refresh_token(user: ModelUser):
    access_token = AccesToken(user)
    refresh_token = RefreshToken(user)
    access_token.save_to_user()
    refresh_token.save_to_user()
    return access_token, refresh_token
def login(mail: str, password: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == mail).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not verify_password(password, user.password):
        raise AuthenticationException("Incorrect password")
    if not user.is_verified:
        raise InvalidDataException("User not verified")
    access_token, refresh_token = create_access_and_refresh_token(user)
    return {
        "user_id": user.id,
        "access_token": access_token.to_token(),
        "refresh_token": refresh_token.to_token(),
        "token_type": "Bearer"
    }


def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    data = get_data_from_token(refresh_token, True)
    if data is None:
        raise InvalidDataException("Invalid token")
    user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not (refresh_token == user.refresh_token):
        raise InvalidDataException("Invalid token")
    acces_token, refresh_token = create_access_and_refresh_token(user) 
    return acces_token.to_token(), refresh_token.to_token()


def reset_password(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not user.is_verified:
        raise InvalidDataException("User not verified")
    acces_token, refresh_token = create_access_and_refresh_token(user) 
    ResetPassToken(user).save_to_user()
    send_password_reset_email(user)
    return {"success": True}


def confirm_reset_password(token: str,
                           password: str,
                           db: Session = Depends(get_db)):
    data = get_data_from_token(token, special=True)
    if data is None:
        raise InvalidDataException("Invalid token")
    if data.expt < datetime.utcnow().isoformat():
        raise InvalidDataException("Token expired")
    user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not (token == user.rest_password_token):
        raise InvalidDataException("Invalid token")
    user.password = get_password_hash(password)
    user.rest_password_token = None
    db.commit()
    db.refresh(user)
    return {"success": True}


def get_me(data: TokenData, db: Session = Depends(get_db)):
    if data.type == UserType.HACKER.value:
        return db.query(ModelHacker).filter(
            ModelHacker.id == data.user_id).first()
    elif data.type == UserType.LLEIDAHACKER.value:
        return db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == data.user_id).first()
    elif data.type == UserType.COMPANYUSER.value:
        return db.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == data.user_id).first()
    else:
        raise InputException("Invalid token")


def verify_user(token: str, db: Session = Depends(get_db)):
    data = get_data_from_token(token, special=True)
    user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    if user.is_verified:
        raise InvalidDataException("User already verified")
    if user.verification_token != token:
        raise InvalidDataException("Invalid token")
    if data.expt < datetime.utcnow().isoformat():
        raise InvalidDataException("Token expired")
    user.is_verified = True
    user.verification_token = None
    db.commit()
    db.refresh(user)
    return {"success": True}


def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    # return user
    if user is None:
        raise InvalidDataException("User not found")
    if user.is_verified:
        raise InvalidDataException("User already verified")
    create_all_tokens(user, db, verification=True)
    send_registration_confirmation_email(user)
    return {"success": True}


def contact(name: str, email: str, title: str, message: str):
    send_contact_email(name, email, title, message)
    return {"success": True}
