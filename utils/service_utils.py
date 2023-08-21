import string
import random
import base64

from error.ValidationException import ValidationException


def set_existing_data(db_obj, req_obj):
    data = req_obj.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_obj, key, value)
    return list(data.keys())


def generate_random_code(length):
    return ''.join(
        random.choice(string.ascii_uppercase) for _ in range(length))


def isBase64(s):
    try:
        return base64.b64encode(base64.b64decode(s)) == s
    except Exception:
        return False


def check_image(payload):
    if payload.image is not None:
        if payload.image.startswith("https://") or payload.image.startswith(
                "http://"):
            payload.is_image_url = True
        if not payload.is_image_url:
            if not isBase64(payload.image):
                raise ValidationException("Image is not a valid base64 string")
    return payload
