from typing import List, Union

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from generated_src.lleida_hack_mail_api_client.models.mail_create import MailCreate

# from services.mail import send_registration_confirmation_email
from src.impl.Event.schema import EventGet
from src.impl.Hacker.schema import HackerCreate
from src.impl.Hacker.schema import HackerGet
from src.impl.Hacker.schema import HackerGetAll
from src.impl.Hacker.schema import HackerUpdate
from src.impl.Hacker.service import HackerService
from src.impl.HackerGroup.schema import HackerGroupGet
from src.impl.Mail.client import MailClient
from src.impl.Mail.internall_templates import InternalTemplate
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import (AccesToken, BaseToken, RefreshToken,
                             VerificationToken)

router = APIRouter(
    prefix="/hacker",
    tags=["Hacker"],
)

hacker_service = HackerService()
mail_client = MailClient()


@router.post("/signup")
def signup(payload: HackerCreate):
    new_hacker = hacker_service.add_hacker(payload)

    # return new_hacker
    access_token = AccesToken(new_hacker).user_set()
    refresh_token = RefreshToken(new_hacker).user_set()
    verification_token = VerificationToken(new_hacker).user_set()
    mail = mail_client.create_mail(
        MailCreate(template_id=mail_client.get_internall_template_id(
            InternalTemplate.USER_CREATED),
                   reciver_id=str(new_hacker.id),
                   reciver_mail=new_hacker.email,
                   subject='Your User Hacker was created',
                   fields=f'{new_hacker.name},{verification_token}'))
    mail_client.send_mail_by_id(mail.id)
    return {
        "success": True,
        "user_id": new_hacker.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/all", response_model=List[HackerGet])
def get_all(token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_all()


@router.get("/{hackerId}",
            response_model=Union[HackerGetAll, HackerGet])
def get(hackerId: int, token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker(hackerId, token)


@router.put("/{hackerId}")
def update(hackerId: int,
           payload: HackerUpdate,
           token: BaseToken = Depends(JWTBearer())):
    hacker, updated = hacker_service.update_hacker(hackerId, payload, token)
    return {"success": True, "updated_id": hacker.id, "updated": updated}


@router.post("/{userId}/ban")
def ban(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.ban_hacker(userId, token)
    return {"success": True, "banned_id": hacker.id}


@router.post("/{userId}/unban")
def unban(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.unban_hacker(userId, token)
    return {"success": True, "unbanned_id": hacker.id}


@router.delete("/{userId}")
def delete(userId: int, token: BaseToken = Depends(JWTBearer())):
    hacker = hacker_service.remove_hacker(userId, token)
    return {"success": True, "deleted_id": hacker.id}


@router.get("/{userId}/events", response_model=List[EventGet])
def get_events(userId: int, token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker_events(userId)


@router.get("/{userId}/groups", response_model=List[HackerGroupGet])
def get_groups(userId: int, token: BaseToken = Depends(JWTBearer())):
    return hacker_service.get_hacker_groups(userId)


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
