import jwt
from config import Configuration
from error.AuthenticationException import AuthenticationException
from datetime import datetime
from dateutil import parser
from src.impl.User.service import UserService
from src.utils.Base.BaseService import BaseService


class Checker(BaseService):
    SECRET_KEY = Configuration.get("SECURITY", "SECRET_KEY")
    ALGORITHM = Configuration.get("SECURITY", "ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = Configuration.get("SECURITY",
                                                    "ACCESS_TOKEN_EXPIRE_MINUTES")

    SERVICE_TOKEN = Configuration.get("SECURITY", "SERVICE_TOKEN")
    user_service = UserService()

    def is_service_token(self, token:str):
        return token == self.SERVICE_TOKEN
    
    def check_token(self, token:str):
        if self.is_service_token(token):
            return True
        dict = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        user = self.user_service.get_by_id(dict["user_id"])
        if user.type != dict["type"]:
            raise AuthenticationException("Invalid token")
        if user.token != token:
            raise AuthenticationException("Invalid token")
        # Here your code for verifying the token or whatever you use
        if parser.parse(dict["expt"]) < datetime.utcnow():
            raise HTTPException(status_code=401, message="Token expired")
        return True
