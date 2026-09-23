import re

from fastapi.security import HTTPBasic
from passlib.hash import pbkdf2_sha256

sec = HTTPBasic()


def verify_password(plain_password, hashed_password):
    return pbkdf2_sha256.verify(plain_password, hashed_password)
    # return True


def get_password_hash(password):
    return pbkdf2_sha256.hash(password)
    # return password


def validate_password(password: str):
    if not re.search(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\s\S]{8,}$", password):
        raise ValueError(
            "Password must contain at least 8 characters, an uppercase letter, "
            "a lowercase letter and a number"
        )
    return password
