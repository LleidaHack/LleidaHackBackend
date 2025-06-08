from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.configuration.Configuration import Configuration
from src.utils.token import BaseToken

SERVICE_TOKEN = Configuration.security.service_token


class JWTBearer(HTTPBearer):
    def __init__(self, required=True, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.required = required

    async def __call__(self, request: Request):
        if not self.required:
            return True
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        #     return credentials.credentials
        if credentials:
            if not credentials.credentials == SERVICE_TOKEN:
                if not credentials.scheme.lower() == 'bearer':
                    raise HTTPException(
                        status_code=403, detail='Invalid authentication scheme.'
                    )
                if not self.verify_jwt(credentials.credentials):
                    raise HTTPException(
                        status_code=403, detail='Invalid token or expired token.'
                    )
            return BaseToken.get_data(credentials.credentials)
        else:
            raise HTTPException(status_code=403, detail='Invalid authorization code.')

    def verify_jwt(self, jwtoken: str) -> bool:
        is_token_valid: bool = False
        try:
            payload = BaseToken.verify(jwtoken)
        except:
            raise
        if payload:
            is_token_valid = True
        return is_token_valid


# Singleton instance to avoid B008 errors
jwt_bearer = JWTBearer()

# Pre-configured dependency to avoid B008 errors
jwt_dependency = Depends(jwt_bearer)
