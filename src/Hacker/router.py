from src.User.model import User as ModelUser
from src.Hacker.model import Hacker as ModelHacker

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
def signup(payload: SchemaHacker,
                 response: Response,
                 db: Session = Depends(get_db)):
    new_hacker = hacker_service.add_hacker(payload, db)

    # return new_hacker
    access_token, refresh_token = create_all_tokens(new_hacker,
                                                    db,
                                                    verification=True)
    send_registration_confirmation_email(new_hacker)
    return {
        "success": True,
        "user_id": new_hacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all")
def get_hackers(db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return hacker_service.get_all(db)


@router.get("/{hackerId}")
def get_hacker(hackerId: int,
                     response: Response,
                     db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker(hackerId, db,
                                           get_data_from_token(token))


# @router.post("/")
# def add_hacker(payload: SchemaHacker,
#                      response: Response,
#                      db: Session = Depends(get_db),
#                      token: str = Depends(JWTBearer())):
#     new_hacker = hacker_service.add_hacker(payload, db,
#                                                  get_data_from_token(token))
#     return {"success": True, "user_id": new_hacker.id}


@router.put("/{hackerId}")
def update_hacker(hackerId: int,
                        payload: SchemaHackerUpdate,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    hacker, updated = hacker_service.update_hacker(
        hackerId, payload, db, get_data_from_token(token))
    return {"success": True, "updated_id": hacker.id, "updated": updated}


@router.post("/{userId}/ban")
def ban_hacker(userId: int,
                     db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    hacker = hacker_service.ban_hacker(userId, db,
                                             get_data_from_token(token))
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
def unban_hacker(userId: int,
                       response: Response,
                       db: Session = Depends(get_db),
                       token: str = Depends(JWTBearer())):
    hacker = hacker_service.unban_hacker(userId, db,
                                               get_data_from_token(token))
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
def delete_hacker(userId: int,
                        response: Response,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    hacker = hacker_service.remove_hacker(userId, db,
                                                get_data_from_token(token))
    return {"success": True, "deleted_id": hacker.id}
    # return hacker


@router.get("/{userId}/events")
def get_hacker_events(userId: int,
                            response: Response,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker_events(userId, db)


@router.get("/{userId}/groups")
def get_hacker_groups(userId: int,
                            response: Response,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker_groups(userId, db)


@router.post("/update_all_codes")
def update_all_codes(db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return hacker_service.update_all_codes(get_data_from_token(token),
                                                 db)
