from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import create_token_pair
import services.user as user_service
from utils.auth_bearer import JWTBearer

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.post("/signup")
async def signup(payload: SchemaUser,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_user = await user_service.add_user(db, payload)
    access_token, refresh_token = create_token_pair(new_user, db)
    return {
        "success": True,
        "user_id": new_user.id,
        "acces_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all")
async def get_users(db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return await user_service.get_all(db)


@router.get("/{userId}")
async def get_user(userId: int,
                   response: Response,
                   db: Session = Depends(get_db),
                   str=Depends(JWTBearer())):
    return await user_service.get_user(db, userId)


@router.post("/")
async def add_user(payload: SchemaUser,
                   response: Response,
                   db: Session = Depends(get_db),
                   str=Depends(JWTBearer())):
    new_user = await user_service.add_user(db, payload)
    return {"success": True, "user_id": new_user.id}


@router.put("/{userId}")
async def update_user(userId: int,
                      payload: SchemaUser,
                      response: Response,
                      db: Session = Depends(get_db),
                      str=Depends(JWTBearer())):
    return await user_service.update_user(db, userId, payload)


@router.delete("/{userId}")
async def delete_user(userId: int,
                      response: Response,
                      db: Session = Depends(get_db),
                      str=Depends(JWTBearer())):
    return await user_service.delete_user(db, userId)
