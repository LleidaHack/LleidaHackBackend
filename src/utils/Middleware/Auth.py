from time import time

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED


def _load_public_key(cert_path: str):
    with open(cert_path) as f:
        cert = f.read()
        return load_pem_x509_certificate(
            bytes(cert, 'utf-8'), default_backend()
        ).public_key()


class JWTConfig:
    def __init__(self, cert_path: str, algorithms: list[str]):
        self.public_key = _load_public_key(cert_path)
        self.algorithms = algorithms


def _decrypt_jwt(config: JWTConfig, token: str):
    return jwt.decode(token, config.public_key, algorithms=config.algorithms)


class JWTAuthorisation(BaseHTTPMiddleware):
    def __init__(self, app, config: JWTConfig):
        self.config = config
        self.bearer = HTTPBearer(auto_error=True)
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: callable):
        try:
            credentials = await self.bearer(request)
            decrypted = _decrypt_jwt(self.config, credentials.credentials)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={'detail': e.detail})
        except JWTError:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={'detail': 'Failed to decrypt JWT'},
            )

        if 'expires' in decrypted and decrypted['expires'] <= time():
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED, content={'detail': 'JWT expired'}
            )

        request.state.jwt_data = decrypted

        return await call_next(request)
