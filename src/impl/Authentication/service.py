from datetime import datetime, UTC

from fastapi_sqlalchemy import db
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate
from src.configuration.Settings import settings
from src.impl.Authentication.schema import ContactMail
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate

from src.impl.User.service import UserService
from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.impl.User.model import User
from src.utils.Base.BaseClient import BaseClient
from src.utils.Base.BaseService import BaseService
from src.utils.security import get_password_hash, verify_password
from src.utils.UserType import UserType
from src.utils.Token import (
    AccesToken,
    BaseToken,
    RefreshToken,
    ResetPassToken,
    VerificationToken,
)


class AuthenticationService(BaseService):
    name = "auth_service"

    user_service: UserService = None
    hacker_service = None
    lleidaHacker_service = None
    companyUser_service = None
    mail_client: MailClient = MailClient()

    def create_access_and_refresh_token(self, user: User):
        access_token = AccesToken(user)
        refresh_token = RefreshToken(user)
        user.token = access_token.to_token()
        user.refresh_token = refresh_token.to_token()
        db.session.commit()
        return access_token, refresh_token

    @BaseService.needs_service(UserService)
    def login(self, mail: str, password: str):
        user = self.user_service.get_by_email(mail)
        if not verify_password(password, user.password):
            raise AuthenticationException("Incorrect password")
        if not user.is_verified and not user.is_deleted:
            raise AuthenticationException("Email verification required", code="EMAIL_NOT_VERIFIED")
        if not BaseToken.is_available(user):
            raise AuthenticationException("Account is not available")
        access_token, refresh_token = self.create_access_and_refresh_token(user)
        return {
            "user_id": user.id,
            "access_token": access_token.to_token(),
            "refresh_token": refresh_token.to_token(),
            "token_type": "Bearer",
        }

    @BaseService.needs_service(UserService)
    def refresh_token(self, refresh_token: RefreshToken):
        user = self.user_service.get_for_update(refresh_token.user_id)
        if not BaseToken.is_available(user):
            raise AuthenticationException("Account is not available")
        if not (refresh_token.to_token() == user.refresh_token):
            raise InvalidDataException("Invalid token")
        acces_token, refresh_token = self.create_access_and_refresh_token(user)
        return {
            "user_id": user.id,
            "access_token": acces_token.to_token(),
            "refresh_token": refresh_token.to_token(),
            "token_type": "Bearer",
        }

    @BaseClient.needs_client(MailClient)
    @BaseService.needs_service(UserService)
    def reset_password(self, email: str):
        user = self.user_service.get_by_email(email, False)
        if user is None or not user.is_verified or user.is_deleted:
            return {"success": True}
        reset_pass_token = ResetPassToken(user).user_set()
        mail = self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.RESET_PASSWORD
                ),
                receiver_id=str(user.id),
                receiver_mail=str(user.email),
                subject="Reset password mail",
                fields=f"{user.name},{reset_pass_token}",
            )
        )
        self.mail_client.send_mail_by_id(mail.id)
        return {"success": True}

    @BaseService.needs_service(UserService)
    def confirm_reset_password(self, token: ResetPassToken, password: str):
        if token.expt < datetime.now(UTC).isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_for_update(token.user_id)
        if not (token.to_token() == user.rest_password_token):
            raise InvalidDataException("Invalid token")
        user.password = get_password_hash(password)
        user.rest_password_token = None
        self.user_service.revoke_tokens(user)
        db.session.commit()
        db.session.refresh(user)
        return {"success": True}

    @BaseService.needs_service(UserService)
    def get_me(self, token: AccesToken):
        return self.user_service.get_by_id(token.user_id)

    @BaseService.needs_service(UserService)
    def verify_user(self, token: VerificationToken):
        if token.expt < datetime.now(UTC).isoformat():
            raise InvalidDataException("Token expired")
        user = self.user_service.get_for_update(token.user_id)
        if user.verification_token != token.to_token():
            raise InvalidDataException("Invalid token")
        self.user_service._verify_user(token.user_id)
        db.session.refresh(user)
        if not BaseToken.is_available(user):
            return {"success": True}
        access_token, refresh_token = self.create_access_and_refresh_token(user)
        return {"success": True, "user_id": user.id,
                "access_token": access_token.to_token(),
                "refresh_token": refresh_token.to_token(), "token_type": "Bearer"}

    @BaseService.needs_service(UserService)
    def force_verification(self, user_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        user = self.user_service.get_by_id(user_id)
        if user.is_deleted:
            raise InvalidDataException("Account is not available")
        if not user.is_verified:
            self.user_service._verify_user(user_id)
        return {"success": True}

    @BaseService.needs_service(UserService)
    def resend_verification(self, email: str):
        user = self.user_service.get_by_email(email)
        if user.is_verified:
            raise InvalidDataException("User already verified")
        verification_token = VerificationToken(user).user_set()
        mail = self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.USER_CREATED
                ),
                receiver_id=str(user.id),
                receiver_mail=user.email,
                subject="Your User Hacker was created",
                fields=f"{user.name},{verification_token}",
            )
        )
        self.mail_client.send_mail_by_id(mail.id)
        return {"success": True}

    @BaseClient.needs_client(MailClient)
    def contact(self, payload: ContactMail):
        mail = self.mail_client.create_mail(
            MailCreate(
                template_id=self.mail_client.get_internall_template_id(
                    InternalTemplate.CONTACT),
                receiver_mail=settings.contact_mail,
                subject=f'Contact {payload.title}',
                fields=
                f'{payload.name},{payload.email},{payload.title},{payload.message}'
            ))
        self.mail_client.send_mail_by_id(mail.id)
        return {
            "success": mail is not None,
            "id": mail.id if mail is not None else None,
        }
