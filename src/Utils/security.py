from fastapi.security import OAuth2PasswordBearer, HTTPBasic
from passlib.hash import pbkdf2_sha256

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
sec = HTTPBasic()


def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)
    # return True


def get_password_hash(password):
    return pbkdf2_sha256.hash(password)
    # return password