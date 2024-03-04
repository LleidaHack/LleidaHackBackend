from typing import List, Union
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from src.utils.database import get_db
from src.utils.Token import AccesToken, BaseToken, RefreshToken, VerificationToken
from src.utils.JWTBearer import JWTBearer

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
def signup(payload: HackerCreateSchema):
    new_hacker = hacker_service.add_hacker(payload)

    # return new_hacker
    access_token = AccesToken(new_hacker).user_set(new_hacker)
    refresh_token = RefreshToken(new_hacker).user_set(new_hacker)
    VerificationToken(new_hacker).user_set(new_hacker)
    send_registration_confirmation_email(new_hacker)
    return {
        "success": True,
        "user_id": new_hacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[HackerGetSchema])
def get_hackers(token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_all()


@router.get("/{hackerId}",
            response_model=Union[HackerGetAllSchema, HackerGetSchema])
def get_hacker(hackerId: int, token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker(hackerId, token)


@router.put("/{hackerId}")
def update_hacker(hackerId: int,
                  payload: HackerUpdateSchema,
                  token: BaseToken = Depends(JWTBearer())):
    hacker, updated = hacker_service.update_hacker(hackerId, payload, token)
    return {"success": True, "updated_id": hacker.id, "updated": updated}


@router.post("/{userId}/ban")
def ban_hacker(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.ban_hacker(userId, token)
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
def unban_hacker(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.unban_hacker(userId, token)
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
def delete_hacker(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.remove_hacker(userId, token)
    return {"success": True, "deleted_id": hacker.id}


@router.get("/{userId}/events", response_model=List[EventGetSchema])
def get_hacker_events(userId: int, token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker_events(userId)


@router.get("/{userId}/groups", response_model=List[HackerGroupGetSchema])
def get_hacker_groups(userId: int,
                      db: Session = Depends(get_db),
                      token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker_groups(userId, db)


# @router.put("/{hacker_id}/register/{event_id}")
# def register_hacker_to_event(event_id: int,
#                              hacker_id: str,
#                              registration: EventRegistrationSchema,
#                              token: BaseToken = Depends(JWTBearer())):
#     """
#     Register a hacker to an event
#     """
#     # event = event_service.get_event(event_id)
#     # hacker = hacker_service.get_hacker(hacker_id, token)
#     return hacker_service.register_hacker_to_event(registration, hacker_id, event_id, token)

# @router.put("/{hacker_id}/unregister/{event_id}")
# def unregister_hacker_from_event(event_id: int,
#                                  hacker_id: int,
#                                  token: BaseToken = Depends(JWTBearer())):
#     """
#     Unregister a hacker from an event
#     """
#     # event = event_service.get_event(event_id, db)
#     # if event is None:
#     #     raise NotFoundException("Event not found")
#     # hacker = hacker_service.get_hacker(hacker_id, db,
#     #                                    get_data_from_token(token))
#     # if hacker is None:
#     #     raise NotFoundException("Hacker not found")
#     return hacker_service.unregister_hacker_from_event(hacker_id, event_id, token)

# @router.post("/update_all_codes")
# def update_all_codes(db: Session = Depends(get_db),
#                            token: BaseToken = Depends(JWTBearer())):
#     return hacker_service.update_all_codes(oken)
