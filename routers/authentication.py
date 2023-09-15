from datetime import timedelta
from models.User import User as ModelUser

from schemas.User import User as SchemaUser

from fastapi import Depends, APIRouter
from database import get_db
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasicCredentials
from security import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, sec, create_token_pair

from error.AuthenticationException import AuthenticationException
from services import authentication as auth_service
from utils.auth_bearer import JWTBearer

router = APIRouter(
    prefix="",
    tags=["Authentication"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/login")
async def login(credentials: HTTPBasicCredentials = Depends(sec),
                db: Session = Depends(get_db)):
    username = credentials.username
    password = credentials.password
    user = authenticate_user(username, password, db)
    if not user:
        raise AuthenticationException("Incorrect username or password")
    access_token, refresh_token = await create_token_pair(user, db)
    return {
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh-token")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return await auth_service.refresh_token(refresh_token, db)


# @router.get("/me")
# async def read_users_me(current_user: ModelUser = Depends(get_current_active_user)):
#     return current_user


@router.post("/confirm-email")
async def confirm_email(email: str, db: Session = Depends(get_db)):
    user = db.query(ModelUser).filter(ModelUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.active = True
    db.commit()
    return {"message": "User email confirmed"}

@router.post("/me")
async def me(db: Session = Depends(get_db), token: str = Depends(JWTBearer())):
    return await auth_service.get_me(token, db)