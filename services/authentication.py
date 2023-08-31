from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from models.User import User as ModelUser
from security import create_token_pair, get_data_from_token


async def refresh_token(token: str,
                        refresh_token: str,
                        db: Session = Depends(get_db)):
    data = get_data_from_token(token)
    if data is None:
        return {"success": False}
    user = db.query(ModelUser).filter(ModelUser.id == data["user_id"]).first()
    if user is None:
        return {"success": False}
    if not (token == user.token and refresh_token == user.refresh_token):
        return {"success": False}
    return create_token_pair(user)
