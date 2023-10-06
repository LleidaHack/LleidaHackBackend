from datetime import datetime, timedelta
from dateutil import parser
from typing import List
from database import get_db
from fastapi.security import OAuth2PasswordBearer, HTTPBasic
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256
import os

from models.User import User as ModelUser
from models.UserType import UserType
from schemas.Token import TokenData
from models.TokenData import TokenData as TD
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
        raise HTTPException(status_code=401, detail="Token expired")
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
    to_encode = {
        'user_id': user.id,
        'email': user.email,
        'type': user.type,
        "is_verified": user.is_verified
    }
    # return "test- "+ ACCESS_TOKEN_EXPIRE_MINUTES
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    if user.type == UserType.HACKER.value:
        to_encode.update({"banned": user.banned})
    elif user.type == UserType.LLEIDAHACKER.value:
        to_encode.update(
            {"active": user.active and user.accepted and not user.rejected})
    elif user.type == UserType.COMPANYUSER.value:
        to_encode.update({"active": user.active})
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    update_tokens(user.id, db, access_token=encoded_jwt)

    return encoded_jwt


def create_refresh_token(user: ModelUser,
                         db: Session,
                         expires_delta: timedelta = None):
    to_encode = {'user_id': user.id, 'email': user.email, 'type': user.type}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    update_tokens(user.id, db, refresh_token=encoded_jwt)
    return encoded_jwt


def create_verification_token(user: ModelUser, db: Session):
    to_encode = {'user_id': user.id, 'type': user.type}
    #expire in 10 minutes
    expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    update_tokens(user.id, db, verification_token=encoded_jwt)
    return encoded_jwt


def create_reset_password_token(user: ModelUser, db: Session):
    to_encode = {'user_id': user.id, 'type': user.type}
    #expire in 10 minutes
    expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    update_tokens(user.id, db, reset_pass_token=encoded_jwt)


def generate_assistance_token(user_id: int, event_id: int, db: Session):
    to_encode = {'user_id': user_id, 'event_id': event_id}
    #expire in 5 days
    expire = datetime.utcnow() + timedelta(days=5)
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_data_from_token(token: str = Depends(oauth2_scheme),
                        refresh: bool = False,
                        special: bool = False):
    d = TD()
    if is_service_token(token):
        d.is_admin = True
        d.is_service = True
        d.user_id = 0
        d.available = True
        d.type = "service"
        d.email = ""
        return d
    data = decode_token(token)
    d.user_id = data.get("user_id")
    d.type = data.get("type")
    if not special:
        d.email = data.get("email")
    else:
        d.expt = data.get("expt")
        try:
            d.event_id = data.get("event_id")
        except:
            pass
    if not refresh and not special:
        d.is_verified = data.get("is_verified")
        if d.type == UserType.HACKER.value:
            d.available = not data.get("banned")
        elif d.type == UserType.LLEIDAHACKER.value:
            d.available = bool(data.get("active"))
        elif d.type == UserType.COMPANYUSER.value:
            d.available = bool(data.get("active"))
    return d


def decode_token(token):
    return jwt.decode(token.encode('utf-8'),
                      SECRET_KEY,
                      algorithms=[ALGORITHM])


# async def check_permissions(token: str, permission: List):
#     if token.credentials == SERVICE_TOKEN:
#         return True
#     jwt_token = jwt.decode(token.credentials.encode('utf-8'),
#                            SECRET_KEY,
#                            algorithms=[ALGORITHM])
#     if jwt_token["type"] not in permission and parser.parse(
#             jwt_token['expt']) < datetime.utcnow():
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Insufficient permissions",
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
