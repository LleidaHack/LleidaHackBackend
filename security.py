from datetime import datetime, timedelta
from dateutil import parser
from typing import List
from database import get_db
from fastapi.security import OAuth2PasswordBearer, HTTPBasic
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt
from passlib.hash import pbkdf2_sha256
import os

from src.impl.User.model import User as ModelUser
from src.utils.Token.model import AccesToken, AsistenceToken, BaseToken, RefreshToken, ResetPassToken, VerificationToken
from utils.UserType import UserType
from utils.TokenData import TokenData as TD
from config import Configuration

from error import AuthenticationException, NotFoundException

SECRET_KEY = Configuration.get("SECURITY", "SECRET_KEY")
ALGORITHM = Configuration.get("SECURITY", "ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.get("SECURITY",
                                                "ACCESS_TOKEN_EXPIRE_MINUTES")

SERVICE_TOKEN = Configuration.get("SECURITY", "SERVICE_TOKEN")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
sec = HTTPBasic()


def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)
    # return True


def get_password_hash(password):
    return pbkdf2_sha256.hash(password)
    # return password


def is_service_token(token: str):
    return token == SERVICE_TOKEN


def get_user(user_id: int, db: Session):
    user = db.query(ModelUser).filter(ModelUser.id == user_id).first()
    if not user:
        raise NotFoundException("User not found")
    return user


def verify_token(token: str, db: Session):
    # token = req.headers["Authorization"]
    if is_service_token(token):
        return True
    dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user = get_user(dict["user_id"], db)
    if user.type != dict["type"]:
        raise AuthenticationException("Invalid token")
    if user.token != token:
        raise AuthenticationException("Invalid token")
    # Here your code for verifying the token or whatever you use
    if parser.parse(dict["expt"]) < datetime.utcnow():
        raise HTTPException(status_code=401, message="Token expired")
    return True


def update_tokens(user_id: int,
                  db: Session,
                  access_token: str = None,
                  refresh_token: str = None,
                  verification_token: str = None,
                  reset_pass_token: str = None):
    user = get_user(user_id, db)
    if access_token is not None:
        user.token = access_token
    if refresh_token is not None:
        user.refresh_token = refresh_token
    if verification_token is not None:
        user.verification_token = verification_token
    if reset_pass_token is not None:
        user.rest_password_token = reset_pass_token
    db.commit()
    db.refresh(user)


def create_access_token(user: ModelUser,
                        db: Session,
                        expires_delta: timedelta = None):
    
    encoded_jwt = AccesToken(user).to_token()
    update_tokens(user.id, db, access_token=encoded_jwt)
    return encoded_jwt


def create_refresh_token(user: ModelUser,
                         db: Session,
                         expires_delta: timedelta = None):
    encoded_jwt = RefreshToken(user).to_token()
    update_tokens(user.id, db, refresh_token=encoded_jwt)
    return encoded_jwt


def create_verification_token(user: ModelUser, db: Session):
    encoded_jwt = VerificationToken(user).to_token()
    update_tokens(user.id, db, verification_token=encoded_jwt)
    return encoded_jwt


def create_reset_password_token(user: ModelUser, db: Session):
    encoded_jwt = ResetPassToken(user).to_token()
    update_tokens(user.id, db, reset_pass_token=encoded_jwt)


def generate_assistance_token(user_id: int, event_id: int, db: Session):
    encoded_jwt = AsistenceToken(user, event_id).to_token()
    return encoded_jwt


def get_data_from_token(token: str = Depends(oauth2_scheme),
                        refresh: bool = False,
                        special: bool = False):
    return BaseToken.to_data(token)


def decode_token(token):
    return jwt.decode(token.encode('utf-8'),
                      SECRET_KEY,
                      algorithms=[ALGORITHM])


# def check_permissions(token: str, permission: List):
#     if token.credentials == SERVICE_TOKEN:
#         return True
#     jwt_token = jwt.decode(token.credentials.encode('utf-8'),
#                            SECRET_KEY,
#                            algorithms=[ALGORITHM])
#     if jwt_token["type"] not in permission and parser.parse(
#             jwt_token['expt']) < datetime.utcnow():
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             message="Insufficient permissions",
#             headers={"WWW-Authenticate": "Bearer"},
#         )


def create_all_tokens(user: ModelUser,
                      db: Session,
                      reset_password: bool = False,
                      verification: bool = False):
    if reset_password:
        create_reset_password_token(user, db)
        return
    if not user.is_verified and verification:
        create_verification_token(user, db)
    access_token = create_access_token(user, db)
    refresh_token = create_refresh_token(user, db)
    return access_token, refresh_token
