from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import check_permissions, create_access_token, oauth_schema, create_refresh_token
import services.user as user_service 

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.post("/signup")
async def signup(payload: SchemaUser, response: Response, db: Session = Depends(get_db)):
    new_user = await user_service.add_user(db, payload)
    token=create_access_token(new_user)
    refresh_token=create_refresh_token(new_user)
    return {"success": True, "created_id": new_user.id, "token": token, "refresh_token": refresh_token}


@router.get("/all")
async def get_users(db: Session = Depends(get_db), token:str = Depends(oauth_schema)):
    await check_permissions(token, ["lleida_hacker", "admin"])
    return await user_service.get_all(db)

@router.get("/{userId}")
async def get_user(userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return await user_service.get_user(db, userId)

@router.post("/")
async def add_user(payload:SchemaUser, response: Response, db: Session = Depends(get_db),str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    new_user = await user_service.add_user(db, payload)
    return {"success": True, "created_id": new_user.id}

@router.put("/{userId}")
async def update_user(userId: int, payload: SchemaUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return await user_service.update_user(db, userId, payload)

@router.delete("/{userId}")
async def delete_user(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return await user_service.delete_user(db, userId)