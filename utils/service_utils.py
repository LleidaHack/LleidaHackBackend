import string
import random
import base64

from error.ValidationException import ValidationException
from models.User import User


def get_user_by_mail(db, email):
    return db.query(User).filter(User.email == email).first()


def get_user_by_nickname(db, nickname):
    return db.query(User).filter(User.nickname == nickname).first()


def get_user_by_telephone(db, telephone):
    return db.query(User).filter(User.telephone == telephone).first()


async def check_user(db, email, nickname, telephone):
    if get_user_by_mail(db, email) is not None:
        raise ValidationException("Email already exists")
    if get_user_by_nickname(db, nickname) is not None:
        raise ValidationException("Nickname already exists")
    if get_user_by_telephone(db, telephone) is not None:
        raise ValidationException("Telephone already exists")


def set_existing_data(db_obj, req_obj):
    data = req_obj.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_obj, key, value)
    return list(data.keys())


def generate_random_code(length):
    return ''.join(
        random.choice(string.ascii_uppercase) for _ in range(length))


def generate_complex_random_code(length):
    return ''.join(random.choice(string.printable) for _ in range(length))


def isBase64(s):
    return True
    # try:
    #     return base64.b64encode(base64.b64decode(s)) == s
    # except Exception:
    #     return False


def check_image(payload):
    if payload.image is not None:
        if payload.image.startswith("https://") or payload.image.startswith(
                "http://"):
            payload.is_image_url = True
        if not payload.is_image_url:
            if not isBase64(payload.image):
                raise ValidationException("Image is not a valid base64 string")
    return payload


def generate_user_code(db, length=20):
    code = generate_random_code(length)
    while db.query(User).filter(User.code == code).first() is not None:
        code = generate_random_code(length)
    return code


def subtract_lists(list1, list2):
    return [item for item in list1 if item not in list2]
