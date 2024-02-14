from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import get_data_from_token
import services.userConfig as userConfig_service
from utils.auth_bearer import JWTBearer

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/userConfig",
    tags=["UserConfig"],
)

@router.get("/all")
async def get_user(db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return await userConfig_service.get_all(db)


@router.get("/{userId}")
async def get_user(userId: int,
                   db: Session = Depends(get_db),
                   str=Depends(JWTBearer())):
    return await userConfig_service.get_user(db, userId, get_data_from_token(str))


