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

from security import create_all_tokens, get_data_from_token

from error.InputException import InputException
from error.InvalidDataException import InvalidDataException


async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    data = get_data_from_token(refresh_token, True)
    if data is None:
        raise InvalidDataException("Invalid token")
    user = db.query(ModelUser).filter(ModelUser.id == data["user_id"]).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not (refresh_token == user.refresh_token):
        raise InvalidDataException("Invalid token")
    return await create_all_tokens(user)


async def reset_password(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if user is None:
        raise InvalidDataException("User not found")
    if not user.is_verified:
        raise InvalidDataException("User not verified")
    return await create_all_tokens(user, True)


async def confirm_reset_password(token: str,
                                 password: str,
                                 db: Session = Depends(get_db)):
    data = get_data_from_token(token, True)
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
        return await db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == data.user_id).first()
    elif data.type == UserType.COMPANYUSER.value:
        return await db.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == data.user_id).first()
    else:
        raise InputException("Invalid token")


async def verify_user(data: TokenData,
                      token: str,
                      db: Session = Depends(get_db)):
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
    db.commit()
    db.refresh(user)
    return {"success": True}


async def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if user is None:
        raise InvalidDataException("User not found")
    if user.is_verified:
        raise InvalidDataException("User already verified")
    return await create_all_tokens(user, True)
