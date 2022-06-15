from schemas.LleidaHacker import LleidaHacker as SchemaLleidaHacker

from database import get_db
from security import create_access_token, oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

import services.lleidahacker as lleidahacker_service


router = APIRouter(
    prefix="/lleidahacker",
    tags=["LleidaHacker"],
)

@router.post("/signup")
async def signup(payload: SchemaLleidaHacker, response: Response, db: Session = Depends(get_db)):
    new_lleidahacker = lleidahacker_service.add_lleidahacker(db, payload)
    token=create_access_token(new_lleidahacker)
    return {"success": True, "created_id": new_lleidahacker.id, "token": token}

@router.get("/all")
async def get_lleidahacker(db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return lleidahacker_service.get_all(db)

@router.get("/{userId}")
async def get_lleidahacker(userId: int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    return lleidahacker_service.get_lleidahacker(userId, db)

@router.post("/")
async def add_lleidahacker(payload:SchemaLleidaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    new_lleidahacker = lleidahacker_service.add_lleidahacker(db, payload)
    return {"success": True, "created_id": new_lleidahacker.id}

@router.delete("/{userId}")
async def delete_lleidahacker(userId:int, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker = lleidahacker_service.delete_lleidahacker(userId, db)
    return {"success": True, "deleted_id": userId}

@router.put("/{userId}")
async def update_lleidahacker(userId:int, payload: SchemaLleidaHacker, response: Response, db: Session = Depends(get_db), str = Depends(oauth_schema)):
    lleidahacker = lleidahacker_service.update_lleidahacker(userId, db, payload)
    return {"success": True, "updated_id": userId}
