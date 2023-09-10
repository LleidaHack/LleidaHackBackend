from models.User import User as ModelUser
from models.Hacker import Hacker as ModelHacker

from schemas.Hacker import Hacker as SchemaHacker
from schemas.Hacker import HackerUpdate as SchemaHackerUpdate

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import create_token_pair, get_data_from_token

from utils.auth_bearer import JWTBearer
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
    access_token, refresh_token = create_token_pair(new_hacker, db)
    return {
        "success": True,
        "user_id": new_hacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all")
async def get_hackers(db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return await hacker_service.get_all(db)


@router.get("/{hackerId}")
async def get_hacker(hackerId: int,
                     response: Response,
                     db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    return await hacker_service.get_hacker(hackerId, db)


@router.post("/")
async def add_hacker(payload: SchemaHacker,
                     response: Response,
                     db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    new_hacker = await hacker_service.add_hacker(payload, db,
                                                 get_data_from_token(token))
    return {"success": True, "user_id": new_hacker.id}


@router.put("/{hackerId}")
async def update_hacker(hackerId: int,
                        payload: SchemaHackerUpdate,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    hacker = await hacker_service.update_hacker(hackerId, payload, db,
                                                get_data_from_token(token))
    return {"success": True, "updated_id": hacker.id}


@router.post("/{userId}/ban")
async def ban_hacker(userId: int,
                     db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    hacker = await hacker_service.ban_hacker(userId, db,
                                             get_data_from_token(token))
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
async def unban_hacker(userId: int,
                       response: Response,
                       db: Session = Depends(get_db),
                       token: str = Depends(JWTBearer())):
    hacker = await hacker_service.unban_hacker(userId, db,
                                               get_data_from_token(token))
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
async def delete_hacker(userId: int,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    hacker = await hacker_service.remove_hacker(userId, db,
                                                get_data_from_token(token))
    return {"success": True, "deleted_id": hacker.id}


@router.get("/{userId}/events")
async def get_hacker_events(userId: int,
                            response: Response,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    return await hacker_service.get_hacker_events(userId, db)


@router.get("/{userId}/groups")
async def get_hacker_groups(userId: int,
                            response: Response,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    return await hacker_service.get_hacker_groups(userId, db)

@router.put("/{userId}/add_dailyhack")
async def add_dailyhack(userId: int,
                        url: str,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    return await hacker_service.add_dailyhack(userId, db)

@router.put("/{userId}/remove_dailyhack")
async def remove_dailyhack(userId: int,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
     return await hacker_service.remove_dailyhack(userId, db)

@router.put("/{userId}/update_dailyhack")
async def update_dailyhack(userId: int,
                            url: str,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
     return await hacker_service.update_dailyhack(userId, db)