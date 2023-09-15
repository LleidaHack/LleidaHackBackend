from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from models.User import User as ModelUser
from models.TokenData import TokenData
from models.UserType import UserType

from models.Hacker import Hacker as ModelHacker
from models.LleidaHacker import LleidaHacker as ModelLleidaHacker
from models.Company import CompanyUser as ModelCompanyUser

from security import create_token_pair, get_data_from_token


async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    data = get_data_from_token(refresh_token, True)
    if data is None:
        return {"success": False}
    user = db.query(ModelUser).filter(ModelUser.id == data["user_id"]).first()
    if user is None:
        return {"success": False}
    if not (refresh_token == user.refresh_token):
        return {"success": False}
    return await create_token_pair(user)


async def get_me(data: TokenData, db: Session = Depends(get_db)):
    if data.type == UserType.HACKER.value:
        return db.query(ModelHacker).filter(
            ModelHacker.id == data.user_id).first()
    elif data.type == UserType.LLEIDAHACKER.value:
        return await db.query(ModelLleidaHacker).filter(
            ModelLleidaHacker.id == data.user_id).first()
    elif data.type == UserType.COMPANYUSER.value:
        return await db.query(ModelCompanyUser).filter(
            ModelCompanyUser.id == data.user_id).first()
    else:
        return None
