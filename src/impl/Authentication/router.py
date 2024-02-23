from datetime import timedelta
from fastapi import Depends, APIRouter
from fastapi import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session

from security import get_data_from_token, sec
from database import get_db
from src.error.AuthenticationException import AuthenticationException
from src.utils.Token.model import BaseToken
from src.utils.JWTBearer import JWTBearer

from src.impl.Authentication.service import AuthenticationService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthenticationService()


@router.get("/login")
def login(credentials: HTTPBasicCredentials = Depends(sec)):
    username = credentials.username
    password = credentials.password
    return auth_service.login(username, password)


@router.post("/reset-password")
def reset_password(email: str):
    return auth_service.reset_password(email)


@router.post("/confirm-reset-password")
def confirm_reset_password(token: str, password: str):
    return auth_service.confirm_reset_password(token, password)


@router.post("/refresh-token")
def refresh_token(refresh_token: BaseToken = Depends(JWTBearer())):
    return auth_service.refresh_token(refresh_token)


@router.get("/me")
def me(token: BaseToken = Depends(JWTBearer())):
    return auth_service.get_me(token)


@router.post("/verify")
def verify(token: BaseToken):
    return auth_service.verify_user(token)


@router.post("/resend-verification")
def resend_verification(email: str):
    return auth_service.resend_verification(email)


@router.get("/check_token")
def check_token(token: BaseToken = Depends(JWTBearer())):
    return {"success": True}


@router.get("/contact")
def contact(name: str, title: str, email: str, message: str):
    return auth_service.contact(name, title, email, message)
