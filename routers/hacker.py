from models.User import User as ModelUser
from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import Hacker as SchemaHacker
from schemas.Hacker import HackerUpdate as SchemaHackerUpdate

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import create_access_token, oauth_schema, create_refresh_token, get_data_from_token

import services.hacker as hacker_service

router = APIRouter(
    prefix="/hacker",
    tags=["Hacker"],
)


@router.post("/signup")
async def signup(payload: SchemaHacker,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_hacker = await hacker_service.add_hacker(payload, db)
    token = create_access_token(new_hacker)
    refresh_token = create_refresh_token(new_hacker)
    return {
        "success": True,
        "created_id": new_hacker.id,
        "token": token,
        "refresh_token": refresh_token
    }


@router.get("/all")
async def get_hackers(db: Session = Depends(get_db),
                      token: str = Depends(oauth_schema)):
    return await hacker_service.get_all(db, get_data_from_token(token))


@router.get("/{hackerId}")
async def get_hacker(hackerId: int,
                     response: Response,
                     db: Session = Depends(get_db),
                     token: str = Depends(oauth_schema)):
    return await hacker_service.get_hacker(hackerId, db)


@router.post("/")
async def add_hacker(payload: SchemaHacker,
                     response: Response,
                     db: Session = Depends(get_db),
                     token: str = Depends(oauth_schema)):
    new_hacker = await hacker_service.add_hacker(payload, db,
                                                 get_data_from_token(token))
    return {"success": True, "created_id": new_hacker.id}


@router.put("/{hackerId}")
async def update_hacker(hackerId: int,
                        payload: SchemaHackerUpdate,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(oauth_schema)):
    hacker = await hacker_service.update_hacker(hackerId, payload, db,
                                                get_data_from_token(token))
    return {"success": True, "updated_id": hacker.id}


@router.post("/{userId}/ban")
async def ban_hacker(userId: int,
                     db: Session = Depends(get_db),
                     token: str = Depends(oauth_schema)):
    hacker = await hacker_service.ban_hacker(userId, db,
                                             get_data_from_token(token))
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
async def unban_hacker(userId: int,
                       response: Response,
                       db: Session = Depends(get_db),
                       token: str = Depends(oauth_schema)):
    hacker = await hacker_service.unban_hacker(userId, db,
                                               get_data_from_token(token))
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
async def delete_hacker(userId: int,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(oauth_schema)):
    hacker = await hacker_service.remove_hacker(userId, db,
                                                get_data_from_token(token))
    return {"success": True, "deleted_id": hacker.id}
