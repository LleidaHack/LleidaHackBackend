from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.utils.Configuration import Configuration
from src.utils.Token import BaseToken

SERVICE_TOKEN = Configuration.get("SECURITY", "SERVICE_TOKEN")



class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self).__call__(request)
        #     return credentials.credentials
        if credentials:
            if not credentials.credentials == SERVICE_TOKEN:
                if not credentials.scheme.lower() == "bearer":
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid authentication scheme.")
                if not self.verify_jwt(credentials.credentials):
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid token or expired token.")
            return BaseToken.get_data(credentials.credentials)
        else:
            raise HTTPException(status_code=403,
                                detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False
        try:
            payload = BaseToken.verify(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
