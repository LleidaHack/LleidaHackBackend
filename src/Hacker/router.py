from models.User import User as ModelUser
from Hacker.model import Hacker as ModelHacker

from src.Hacker.schema import Hacker as SchemaHacker
from src.Hacker.schema import HackerUpdate as SchemaHackerUpdate

from database import get_db

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import create_all_tokens, get_data_from_token

from utils.auth_bearer import JWTBearer
import Hacker.service as hacker_service

from services.mail import send_registration_confirmation_email

router = APIRouter(
    prefix="/hacker",
    tags=["Hacker"],
)


@router.post("/signup")
async def signup(payload: SchemaHacker,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_hacker = await hacker_service.add_hacker(payload, db)

    # return new_hacker
    access_token, refresh_token = create_all_tokens(new_hacker,
                                                    db,
                                                    verification=True)
    await send_registration_confirmation_email(new_hacker)
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
    return await hacker_service.get_hacker(hackerId, db,
                                           get_data_from_token(token))


# @router.post("/")
# async def add_hacker(payload: SchemaHacker,
#                      response: Response,
#                      db: Session = Depends(get_db),
#                      token: str = Depends(JWTBearer())):
#     new_hacker = await hacker_service.add_hacker(payload, db,
#                                                  get_data_from_token(token))
#     return {"success": True, "user_id": new_hacker.id}


@router.put("/{hackerId}")
async def update_hacker(hackerId: int,
                        payload: SchemaHackerUpdate,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    hacker, updated = await hacker_service.update_hacker(
        hackerId, payload, db, get_data_from_token(token))
    return {"success": True, "updated_id": hacker.id, "updated": updated}


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
    # return hacker


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


@router.post("/update_all_codes")
async def update_all_codes(db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return await hacker_service.update_all_codes(get_data_from_token(token),
                                                 db)
