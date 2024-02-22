from src.impl.User.service import UserService
from src.utils.Base.BaseService import BaseService


class TokenService(BaseService):

    user_service = UserService()
