import string
import random
import base64

from src.impl.User.service import UserService

from src.error.ValidationException import ValidationException

user_service = UserService()


def check_user(email, nickname, telephone):
    if user_service.get_by_email(email, False) is not None:
        raise ValidationException("Email already exists")
    if user_service.get_by_nickname(nickname, False) is not None:
        raise ValidationException("Nickname already exists")
    if user_service.get_by_phone(telephone, False) is not None:
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


def generate_user_code(length=20):
    code = generate_random_code(length)
    while user_service.get_by_code(code, False) is not None:
        code = generate_random_code(length)
    return code


def subtract_lists(list1, list2):
    return [item for item in list1 if item not in list2]
