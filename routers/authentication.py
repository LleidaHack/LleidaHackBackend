from datetime import timedelta
from models.User import User as ModelUser

from schemas.User import User as SchemaUser

from fastapi import Depends, APIRouter
from database import get_db
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasicCredentials
from security import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, get_current_active_user, sec

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
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(user,
                                       expires_delta=access_token_expires)
    return {
        "user_id": user.id,
        "access_token": access_token,
        "token_type": "bearer"
    }


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
