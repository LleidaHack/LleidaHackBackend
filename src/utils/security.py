from fastapi import Depends
from fastapi.security import HTTPBasic
from passlib.hash import pbkdf2_sha256

sec = HTTPBasic()
sec_dependency = Depends(sec)


def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)
    # return True


def get_password_hash(password):
    return pbkdf2_sha256.hash(password)
    # return password
