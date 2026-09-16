from src.utils.Base.BaseException import BaseException


class AuthenticationException(BaseException):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code
