from datetime import datetime

from src.utils.security import get_password_hash, verify_password
from src.utils.UserType import UserType
from src.utils.Base.BaseService import BaseService

from src.impl.User.service import UserService
from services.mail import send_registration_confirmation_email, send_password_reset_email, send_contact_email

from src.error.InputException import InputException
from src.error.InvalidDataException import InvalidDataException
from src.error.AuthenticationException import AuthenticationException

from src.impl.User.model import User as ModelUser
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.LleidaHacker.model import LleidaHacker as ModelLleidaHacker
from src.impl.CompanyUser.model import CompanyUser as ModelCompanyUser
from src.utils.Token import AccesToken, RefreshToken, ResetPassToken, VerificationToken


class AuthenticationService(BaseService):

    user_service = UserService()

    def create_access_and_refresh_token(self, user: ModelUser):
        access_token = AccesToken(user)
        refresh_token = RefreshToken(user)
        access_token.save_to_user()
        refresh_token.save_to_user()
        return access_token, refresh_token

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

    def refresh_token(self, refresh_token: RefreshToken):
        user = self.user_service.get_user_by_id(refresh_token.user_id)
        if not (refresh_token.to_token() == user.refresh_token):
            raise InvalidDataException("Invalid token")
        acces_token, refresh_token = self.create_access_and_refresh_token(user)
        return acces_token.to_token(), refresh_token.to_token()

    def reset_password(self, email: str):
        user = self.user_service.get_user_by_email(email)
        if not user.is_verified:
            raise InvalidDataException("User not verified")
        self.create_access_and_refresh_token(user)
        ResetPassToken(user).save_to_user()
        send_password_reset_email(user)
        return {"success": True}

    def confirm_reset_password(self, token: ResetPassToken, password: str):
        if token.expt < datetime.utcnow().isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_user_by_id(token.user_id)
        if not (token.to_token() == user.rest_password_token):
            raise InvalidDataException("Invalid token")
        user.password = get_password_hash(password)
        user.rest_password_token = None
        self.db.commit()
        self.db.refresh(user)
        return {"success": True}

    def get_me(self, token: AccesToken):
        if token.user_type == UserType.HACKER.value:
            return self.db.query(ModelHacker).filter(
                ModelHacker.id == token.user_id).first()
        elif token.user_type == UserType.LLEIDAHACKER.value:
            return self.db.query(ModelLleidaHacker).filter(
                ModelLleidaHacker.id == token.user_id).first()
        elif token.user_type == UserType.COMPANYUSER.value:
            return self.db.query(ModelCompanyUser).filter(
                ModelCompanyUser.id == token.user_id).first()
        else:
            raise InputException("Invalid token")

    def verify_user(self, token: VerificationToken):
        if token.expt < datetime.utcnow().isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_user_by_id(token.user_id)
        if user.is_verified:
            raise InvalidDataException("User already verified")
        if user.verification_token != token.to_token():
            raise InvalidDataException("Invalid token")
        user.is_verified = True
        user.verification_token = None
        self.db.commit()
        self.db.refresh(user)
        return {"success": True}

    def resend_verification(self, email: str):
        user = self.user_service.get_user_by_email(email)
        if user.is_verified:
            raise InvalidDataException("User already verified")
        AccesToken(user).save_to_user()
        RefreshToken(user).save_to_user()
        VerificationToken(user).save_to_user()
        send_registration_confirmation_email(user)
        return {"success": True}

    def contact(name: str, email: str, title: str, message: str):
        send_contact_email(name, email, title, message)
        return {"success": True}
