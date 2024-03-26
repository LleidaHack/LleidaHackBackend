from datetime import datetime

from fastapi_sqlalchemy import db

import src.impl.User.service as U_S
from services.mail import (send_contact_email, send_password_reset_email,
                           send_registration_confirmation_email)
from src.error.AuthenticationException import AuthenticationException
from src.error.InputException import InputException
from src.error.InvalidDataException import InvalidDataException
from src.impl.User.model import User as ModelUser
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash, verify_password
from src.utils.Token import (AccesToken, BaseToken, RefreshToken,
                             ResetPassToken, VerificationToken)
from src.utils.UserType import UserType


class AuthenticationService(BaseService):
    name = 'auth_service'

    user_service = None
    hacker_service = None
    lleidaHacker_service = None
    companyUser_service = None

    def create_access_and_refresh_token(self, user: ModelUser):
        access_token = AccesToken(user)
        refresh_token = RefreshToken(user)
        access_token.user_set()
        refresh_token.user_set()
        return access_token, refresh_token

    @BaseService.needs_service(U_S.UserService)
    def login(self, mail: str, password: str):
        user = self.user_service.get_user_by_email(mail)
        if not verify_password(password, user.password):
            raise AuthenticationException("Incorrect password")
        if not user.is_verified:
            raise InvalidDataException("User not verified")
        access_token, refresh_token = self.create_access_and_refresh_token(
            user)
        return {
            "user_id": user.id,
            "access_token": access_token.to_token(),
            "refresh_token": refresh_token.to_token(),
            "token_type": "Bearer"
        }

    @BaseService.needs_service(U_S.UserService)
    def refresh_token(self, refresh_token: RefreshToken):
        user = self.user_service.get_by_id(refresh_token.user_id)
        if not (refresh_token.to_token() == user.refresh_token):
            raise InvalidDataException("Invalid token")
        acces_token, refresh_token = self.create_access_and_refresh_token(user)
        return acces_token.to_token(), refresh_token.to_token()

    @BaseService.needs_service(U_S.UserService)
    def reset_password(self, email: str):
        user = self.user_service.get_user_by_email(email)
        if not user.is_verified:
            raise InvalidDataException("User not verified")
        self.create_access_and_refresh_token(user)
        ResetPassToken(user).user_set()
        send_password_reset_email(user)
        return {"success": True}

    @BaseService.needs_service(U_S.UserService)
    def confirm_reset_password(self, token: ResetPassToken, password: str):
        if token.expt < datetime.utcnow().isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_by_id(token.user_id)
        if not (token.to_token() == user.rest_password_token):
            raise InvalidDataException("Invalid token")
        user.password = get_password_hash(password)
        user.rest_password_token = None
        db.session.commit()
        db.session.refresh(user)
        return {"success": True}

    def get_me(self, token: AccesToken):
        if token.user_type == UserType.HACKER.value:
            return self.hacker_service.get_by_id(token.user_id)
        elif token.user_type == UserType.LLEIDAHACKER.value:
            return self.lleidaHacker_service.get_by_id(token.user_id)
        elif token.user_type == UserType.COMPANYUSER.value:
            return self.companyUser_service.get_by_id(token.user_id)
        else:
            raise InputException("Invalid token")

    @BaseService.needs_service(U_S.UserService)
    def verify_user(self, token: VerificationToken):
        if token.expt < datetime.utcnow().isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_by_id(token.user_id)
        if user.verification_token != token.to_token():
            raise InvalidDataException("Invalid token")
        return self.user_service._verify_user(token.user_id)
        return {"success": True}
    

    @BaseService.needs_service(U_S.UserService)
    def force_verification(self, user_id: int, data: BaseToken):
        if not data.is_admin:
            raise AuthenticationException(
                "User don'have permissions to do this")
        self.user_service._verify_user(user_id)
        return {"success": True}

    @BaseService.needs_service(U_S.UserService)
    def resend_verification(self, email: str):
        user = self.user_service.get_user_by_email(email)
        if user.is_verified:
            raise InvalidDataException("User already verified")
        AccesToken(user).user_set()
        RefreshToken(user).user_set()
        VerificationToken(user).user_set()
        send_registration_confirmation_email(user)
        return {"success": True}

    def contact(name: str, email: str, title: str, message: str):
        send_contact_email(name, email, title, message)
        return {"success": True}
