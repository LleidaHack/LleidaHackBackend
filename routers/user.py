from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import get_data_from_token
import services.user as user_service
from utils.auth_bearer import JWTBearer

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.get("/all")
async def get_users(db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return await user_service.get_all(db)


@router.get("/{userId}")
async def get_user(userId: int,
                   db: Session = Depends(get_db),
                   str=Depends(JWTBearer())):
    return await user_service.get_user(db, userId, get_data_from_token(str))


@router.get("/email/{email}")
async def get_user_by_email(email: str,
                            db: Session = Depends(get_db),
                            str=Depends(JWTBearer())):
    return await user_service.get_user_by_email(db, email,
                                                get_data_from_token(str))


@router.get("/nickname/{nickname}")
async def get_user_by_nickname(nickname: str,
                               db: Session = Depends(get_db),
                               str=Depends(JWTBearer())):
    return await user_service.get_user_by_nickname(db, nickname,
                                                   get_data_from_token(str))


@router.get("/phone/{phone}")
async def get_user_by_phone(phone: str,
                            db: Session = Depends(get_db),
                            str=Depends(JWTBearer())):
    return await user_service.get_user_by_phone(db, phone,
                                                get_data_from_token(str))


@router.get("/code/{code}")
async def get_user_by_code(code: str,
                           db: Session = Depends(get_db),
                           str=Depends(JWTBearer())):
    return await user_service.get_user_by_code(db, code,
                                               get_data_from_token(str))


# @router.post("/")
# async def add_user(payload: SchemaUser,
#                    db: Session = Depends(get_db),
#                    str=Depends(JWTBearer())):
#     new_user = await user_service.add_user(db, payload)
#     return {"success": True, "user_id": new_user.id}

# @router.put("/{userId}")
# async def update_user(userId: int,
#                       payload: SchemaUser,
#                       response: Response,
#                       db: Session = Depends(get_db),
#                       str=Depends(JWTBearer())):
#     return await user_service.update_user(db, userId, payload)

# @router.delete("/{userId}")
# async def delete_user(userId: int,
#                       response: Response,
#                       db: Session = Depends(get_db),
#                       str=Depends(JWTBearer())):
#     return await user_service.delete_user(db, userId)
