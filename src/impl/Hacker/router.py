from typing import List, Union
from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session

from database import get_db
from utils.auth_bearer import JWTBearer
from security import create_all_tokens, get_data_from_token

from services.mail import send_registration_confirmation_email
from src.impl.Hacker.service import HackerService

from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.Hacker.schema import HackerGetAll as HackerGetAllSchema
from src.impl.Hacker.schema import HackerCreate as HackerCreateSchema
from src.impl.Hacker.schema import HackerUpdate as HackerUpdateSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema

router = APIRouter(
    prefix="/hacker",
    tags=["Hacker"],
)

hacker_service = HackerService()


@router.post("/signup")
def signup(payload: HackerCreateSchema = Depends(get_db)):
    new_hacker = hacker_service.add_hacker(payload)

    # return new_hacker
    access_token, refresh_token = create_all_tokens(new_hacker,
                                                    hacker_service.db,
                                                    verification=True)
    send_registration_confirmation_email(new_hacker)
    return {
        "success": True,
        "user_id": new_hacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[HackerGetSchema])
def get_hackers(token: str = Depends(JWTBearer())):
    return hacker_service.get_all()


@router.get("/{hackerId}",
            response_model=Union[HackerGetSchema, HackerGetAllSchema])
def get_hacker(hackerId: int, token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker(hackerId, get_data_from_token(token))


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
                  payload: HackerUpdateSchema,
                  token: str = Depends(JWTBearer())):
    hacker, updated = hacker_service.update_hacker(hackerId, payload,
                                                   get_data_from_token(token))
    return {"success": True, "updated_id": hacker.id, "updated": updated}


@router.post("/{userId}/ban")
def ban_hacker(userId: int, token: str = Depends(JWTBearer())):
    hacker = hacker_service.ban_hacker(userId, get_data_from_token(token))
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
def unban_hacker(userId: int, token: str = Depends(JWTBearer())):
    hacker = hacker_service.unban_hacker(userId, get_data_from_token(token))
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
def delete_hacker(userId: int, token: str = Depends(JWTBearer())):
    hacker = hacker_service.remove_hacker(userId, get_data_from_token(token))
    return {"success": True, "deleted_id": hacker.id}
    # return hacker


@router.get("/{userId}/events", response_model=List[EventGetSchema])
def get_hacker_events(userId: int, token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker_events(userId)


@router.get("/{userId}/groups", response_model=List[HackerGroupGetSchema])
def get_hacker_groups(userId: int,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return hacker_service.get_hacker_groups(userId, db)


# @router.post("/update_all_codes")
# def update_all_codes(db: Session = Depends(get_db),
#                            token: str = Depends(JWTBearer())):
#     return hacker_service.update_all_codes(get_data_from_token(token),
#                                                  db)
