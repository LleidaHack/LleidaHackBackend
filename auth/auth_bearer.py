from fastapi import Request, HTTPException
from fastapi.security import OAuth2PasswordBearer

class JWTBearer(HTTPBearer):
    """Attaches JWT Bearer Authentication to the given Request object."""
    def __init__(self, auth_error: bool = True):
        super(JWTBearer, self).__init__(auth_error=auth_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == 'Bearer':
                raise HTTPBadRequest(status_code=403,text='Invalid authorization scheme')
            if not self.verify_jwt(credentials.credentials):
                raise HTTPBadRequest(status_code=403,text='Invalid or expired authorization token')
            return credentials.credentials
        else:
            raise HTTPBadRequest(status_code=403,text='Missing authorization token')
    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid = False
        try:
            payload = decodeJWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid