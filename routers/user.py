from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from security import check_permissions, create_access_token, oauth_schema
import services.user as user_service 

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.post("/signup")
async def signup(payload: SchemaUser, response: Response, db: Session = Depends(get_db)):
    new_user = user_service.add_user(db, payload)
    token=create_access_token(new_user)
    return {"success": True, "created_id": new_user.id, "token": token}


@router.get("/all")
async def get_users(db: Session = Depends(get_db), token:str = Depends(oauth_schema)):
    check_permissions(token, ["lleida_hacker", "admin"])
    return user_service.get_all(db)

@router.get("/{userId}")
async def get_user(userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return user_service.get_user(db, userId)

@router.post("/")
async def add_user(payload:SchemaUser, response: Response, db: Session = Depends(get_db),str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    new_user = user_service.add_user(db, payload)
    return {"success": True, "created_id": new_user.id}

@router.put("/{userId}")
async def update_user(userId: int, payload: SchemaUser, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return user_service.update_user(db, userId, payload)

@router.delete("/{userId}")
async def remove_user(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    check_permissions(str, ["lleida_hacker", "admin"])
    return user_service.remove_user(db, userId)