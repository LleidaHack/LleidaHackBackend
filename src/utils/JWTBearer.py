from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from src.utils.Token import BaseToken
from src.utils.TokenType import TokenType


class JWTBearer(HTTPBearer):
    def __init__(self, required=True, auto_error=True, expected_type=TokenType.ACCESS,
                 require_available=True, allow_service=True):
        super().__init__(auto_error=False)
        self.required = required
        self.expected_type = expected_type
        self.require_available = require_available
        self.allow_service = allow_service

    async def __call__(self, request: Request):
        if not self.required:
            return True
        credentials = await super().__call__(request)
        if credentials is None:
            raise HTTPException(status_code=401, detail="Bearer credentials required")
        return BaseToken.get_data(
            credentials.credentials,
            expected_type=self.expected_type,
            require_available=self.require_available,
            allow_service=self.allow_service,
        )
