from datetime import timedelta
from fastapi import Depends, APIRouter
from fastapi import Depends
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session

from security import get_data_from_token, sec, create_all_tokens
from database import get_db
from error.AuthenticationException import AuthenticationException
from utils.auth_bearer import JWTBearer

from src.Authentication import service as auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# from services.mail import send_registration_confirmation_email, send_password_reset_email

# @router.post("/test")
# def test(id: int, db: Session = Depends(get_db)):
#     user = db.query(ModelUser).filter(ModelUser.id == id).first()
#     send_registration_confirmation_email(user)
#     send_password_reset_email(user)


@router.get("/login")
def login(credentials: HTTPBasicCredentials = Depends(sec),
                db: Session = Depends(get_db)):
    username = credentials.username
    password = credentials.password
    return auth_service.login(username, password, db)


@router.post("/reset-password")
def reset_password(email: str, db: Session = Depends(get_db)):
    return auth_service.reset_password(email, db)


@router.post("/confirm-reset-password")
def confirm_reset_password(token: str,
                                 password: str,
                                 db: Session = Depends(get_db)):
    return auth_service.confirm_reset_password(token, password, db)


@router.post("/refresh-token")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return auth_service.refresh_token(refresh_token, db)


@router.get("/me")
def me(db: Session = Depends(get_db), token: str = Depends(JWTBearer())):
    return auth_service.get_me(get_data_from_token(token), db)


@router.post("/verify")
def verify(token: str, db: Session = Depends(get_db)):
    return auth_service.verify_user(token, db)


@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    return auth_service.resend_verification(email, db)


@router.get("/check_token")
def check_token(token: str = Depends(JWTBearer())):
    return {"success": True}


@router.get("/contact")
def contact(name: str, title: str, email: str, message: str):
    return auth_service.contact(name, title, email, message)
