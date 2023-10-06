from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from models.User import User as ModelUser
from models.TokenData import TokenData
from models.UserType import UserType

from models.Hacker import Hacker as ModelHacker
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.Company import CompanyUser as ModelCompanyUser

from security import create_all_tokens, get_data_from_token, verify_password

from error.InputException import InputException
from error.InvalidDataException import InvalidDataException
from error.AuthenticationException import AuthenticationException

from services.mail import send_registration_confirmation_email, send_password_reset_email, send_contact_email


async def login(mail: str, password: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == mail).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not verify_password(password, user.password):
        raise AuthenticationException("Incorrect password")
    if not user.is_verified:
        raise InvalidDataException("User not verified")
    access_token, refresh_token = create_all_tokens(user, db)
    return {
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }


async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    data = get_data_from_token(refresh_token, True)
    if data is None:
        raise InvalidDataException("Invalid token")
    user = db.query(ModelUser).filter(ModelUser.id == data.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not (refresh_token == user.refresh_token):
        raise InvalidDataException("Invalid token")
    return create_all_tokens(user)


async def reset_password(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not user.is_verified:
        raise InvalidDataException("User not verified")
    create_all_tokens(user, db, True)
    await send_password_reset_email(user)
    return {"success": True}


async def confirm_reset_password(token: str,
                                 password: str,
                                 db: Session = Depends(get_db)):
    data = get_data_from_token(token, special=True)
    if data is None:
        raise InvalidDataException("Invalid token")
    if data.expt < datetime.utcnow().isoformat():
        raise InvalidDataException("Token expired")
    user = db.query(ModelUser).filter(ModelUser.id == data["user_id"]).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not (token == user.reset_password_token):
        raise InvalidDataException("Invalid token")
    user.password = password
    user.reset_password_token = None
    db.commit()
    db.refresh(user)
    return {"success": True}


async def get_me(data: TokenData, db: Session = Depends(get_db)):
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


async def verify_user(token: str, db: Session = Depends(get_db)):
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


async def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    # return user
    if user is None:
        raise InvalidDataException("User not found")
    if user.is_verified:
        raise InvalidDataException("User already verified")
    create_all_tokens(user, db, verification=True)
    await send_registration_confirmation_email(user)
    return {"success": True}


async def contact(name: str, email: str, title: str, message: str):
    await send_contact_email(name, email, title, message)
    return {"success": True}
