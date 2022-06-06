import time
import jwt

JWT_SECRET = config('JWT_SECRET')
JWT_ALGORITHM = 'HS256'

def signJWT(user_id):
    payload = {
        'user_id': user_id,
        'expires': time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    return {'token': token}

def decodeJWT(token):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)
        return decoded_token if decoded_token['expires'] > time.time() else None
    except:
        return {}