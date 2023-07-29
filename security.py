from datetime import datetime, timedelta
from dateutil import parser
from typing import List
from database import db_get, get_db
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPBasic
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256

from models.User import User as ModelUser
from schemas.Token import TokenData
from config import Configuration

SECRET_KEY = Configuration.get("SECURITY", "SECRET_KEY")
ALGORITHM = Configuration.get("SECURITY", "ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.get("SECURITY", "ACCESS_TOKEN_EXPIRE_MINUTES")

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

def verify_token(req: Request):
    token = req.headers["Authorization"]
    if token is SERVICE_TOKEN:
        return True
    dict=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # Here your code for verifying the token or whatever you use
    if parser.parse(dict["expt"]) < datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
    return True

def authenticate_user(username: str, password: str):
    user_dict = db_get().query(ModelUser).filter(ModelUser.email == username).first()
    if not user_dict:
        return False
    if not verify_password(password, user_dict.password):
        return False
    return user_dict

def create_access_token(user:ModelUser , expires_delta: timedelta = None):
    to_encode = {'user_id': user.id, 'email': user.email, 'type': user.type}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"expt": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(user:ModelUser , expires_delta: timedelta = None):
    to_encode = {'user_id': user.id, 'email': user.email, 'type': user.type}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_confirmation_token(email: str):
    serialized_jwt = jwt.encode({"email": email}, SECRET_KEY, algorithm=ALGORITHM)
    return serialized_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user_dict = get_db().query(ModelUser).filter(ModelUser.email == token_data.username).first()
    user = ModelUser(name=user_dict.name, 
                     email=user_dict.email,
                     password=user_dict.password,
                     nickname=user_dict.nickname,
                     birthdate = user_dict.birthdate,
                     food_restrictions=user_dict.food_restrictions,
                     telephone=user_dict.telephone,
                     address=user_dict.address,
                     shirt_size=user_dict.shirt_size
    )
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: ModelUser = Depends(get_current_user)):
    # if current_user.disabled:
        # raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def check_permissions(token:str, permission: List):
    if token.credentials == SERVICE_TOKEN:
        return True
    jwt_token = jwt.decode(token.credentials.encode('utf-8'), SECRET_KEY, algorithms=[ALGORITHM])
    if jwt_token["type"] not in permission and parser.parse(jwt_token['expt']) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
            headers={"WWW-Authenticate": "Bearer"},
        )