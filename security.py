from datetime import datetime, timedelta
from dateutil import parser
from typing import List
from database import get_db
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPBasic
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256
import os

from models.User import User as ModelUser
from schemas.Token import TokenData
from config import Configuration

SECRET_KEY = Configuration.get("SECURITY", "SECRET_KEY")
ALGORITHM = Configuration.get("SECURITY", "ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.get("SECURITY",
                                                "ACCESS_TOKEN_EXPIRE_MINUTES")

SERVICE_TOKEN = Configuration.get("SECURITY", "SERVICE_TOKEN")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth_schema = HTTPBearer()
sec = HTTPBasic()


def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)
    # return True


def get_password_hash(password):
    return pbkdf2_sha256.hash(password)
    # return password


def is_service_token(token: str):
    return token == SERVICE_TOKEN


def verify_token(req: Request):
    token = req.headers["Authorization"]
    if is_service_token(token):
        return True
    dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # Here your code for verifying the token or whatever you use
    if parser.parse(dict["expt"]) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def authenticate_user(username: str, password: str, db: Session):
    user_dict = db.query(ModelUser).filter(ModelUser.email == username).first()
    if not user_dict:
        return False
    if not verify_password(password, user_dict.password):
        return False
    return user_dict


def create_access_token(user: ModelUser, expires_delta: timedelta = None):
    to_encode = {'user_id': user.id, 'email': user.email, 'type': user.type}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    if user.type == "hacker":
        to_encode.update({"banned": user.banned})
    elif user.type == "lleida_hacker":
        to_encode.update({"active": user.active})
    elif user.type == "company":
        to_encode.update({"active": user.active})
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user: ModelUser, expires_delta: timedelta = None):
    to_encode = {'user_id': user.id, 'email': user.email, 'type': user.type}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str):
    serialized_jwt = jwt.encode({"email": email},
                                SECRET_KEY,
                                algorithm=ALGORITHM)
    return serialized_jwt


def get_data_from_token(token: str = Depends(oauth2_scheme)):
    data = decode_token(token)
    d = TokenData()
    if is_service_token(token):
        d.is_admin = True
        d.is_service = True
        d.user_id = 0
        return d
    d.user_id = data.get("user_id")
    d.type = data.get("type")
    if d.type == "hacker":
        d.available = data.get("banned")
    elif d.type == "lleida_hacker":
        d.available = data.get("active")
    elif d.type == "company":
        d.available = data.get("active")
    return d


def decode_token(token):
    return jwt.decode(token.credentials.encode('utf-8'),
                      SECRET_KEY,
                      algorithms=[ALGORITHM])


async def check_permissions(token: str, permission: List):
    if token.credentials == SERVICE_TOKEN:
        return True
    jwt_token = jwt.decode(token.credentials.encode('utf-8'),
                           SECRET_KEY,
                           algorithms=[ALGORITHM])
    if jwt_token["type"] not in permission and parser.parse(
            jwt_token['expt']) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def check_image_exists(image_id: int):
    file_path = f"static/{image_id}.jpg"
    if not os.path.isfile(file_path):
        return False
    return True
