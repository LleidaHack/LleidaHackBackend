from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials

from src.impl.Authentication.schema import ContactMail
from src.impl.Authentication.service import AuthenticationService
from src.utils.JWTBearer import JWTBearer
from src.utils.security import sec
from src.utils.Token import BaseToken

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
    return auth_service.confirm_reset_password(BaseToken.get_data(token),
                                               password)


@router.post("/refresh-token")
def refresh_token(refresh_token: BaseToken = Depends(JWTBearer())):
    return auth_service.refresh_token(refresh_token)


@router.get("/me")
def me(token: BaseToken = Depends(JWTBearer())):
    return auth_service.get_me(token)


@router.post("/verify")
def verify(token: str):
    return auth_service.verify_user(BaseToken.get_data(token))


@router.post("/force-verify/{user_id}")
def force_verify(user_id, token: BaseToken = Depends(JWTBearer())):
    return auth_service.force_verification(user_id, token)


@router.post("/resend-verification")
def resend_verification(email: str):
    return auth_service.resend_verification(email)


@router.get("/check_token")
def check_token(token: BaseToken = Depends(JWTBearer())):
    return {"success": True}


@router.post("/contact")
def contact(payload: ContactMail):
    return auth_service.contact(payload)
