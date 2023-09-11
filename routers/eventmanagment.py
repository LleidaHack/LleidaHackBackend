from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session
from database import get_db
from error.NotFoundException import NotFoundException

from security import get_data_from_token
from schemas.Event import HackerEventRegistration as SchemaEventRegistration
from schemas.Event import HackerEventRegistrationUpdate as SchemaEventRegistrationUpdate
import services.event as event_service
import services.hacker as hacker_service
import services.hackergroup as hackergroup_service
import services.eventmanagment as eventmanagment_service

from utils.auth_bearer import JWTBearer

router = APIRouter(
    prefix="/eventmanagment",
    tags=["EventManagment"],
)

@router.post("/{event_id}/add_dailyhack/{hacker_id}")
async def add_dailyhack(event_id: int,
                        hacker_id: int,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    """
    Add a dailyhack to an event
    """
    return await eventmanagment_service.add_dailyhack(event_id, hacker_id, db, get_data_from_token(token))


@router.put("/{event_id}/register/{hacker_id}")
async def register_hacker_to_event(event_id: int,
                                   hacker_id: int,
                                   registration: SchemaEventRegistration,
                                   db: Session = Depends(get_db),
                                   token: str = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    return await eventmanagment_service.register_hacker_to_event(
        registration, event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/unregister/{hacker_id}")
async def unregister_hacker_from_event(event_id: int,
                                       hacker_id: int,
                                       db: Session = Depends(get_db),
                                       token: str = Depends(JWTBearer())):
    """
    Unregister a hacker from an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.unregister_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/participate/{hacker_id}")
async def participate_hacker_to_event(event_id: int,
                                      hacker_id: int,
                                      db: Session = Depends(get_db),
                                      token: str = Depends(JWTBearer())):
    """
    Participate a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    await eventmanagment_service.participate_hacker_to_event(
        event, hacker, db, get_data_from_token(token))
    return {
        'success': True,
        'event_id': event.id,
        'hacker_id': hacker.id,
        'hacker_name': hacker.name,
        'hacker_shirt_size': hacker.shirt_size
    }


@router.put("/{event_id}/unparticipate/{hacker_id}")
async def unparticipate_hacker_from_event(event_id: int,
                                          hacker_id: int,
                                          db: Session = Depends(get_db),
                                          token: str = Depends(JWTBearer())):
    """
    Unparticipate a hacker from an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    await eventmanagment_service.unparticipate_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/accept/{hacker_id}")
async def accept_hacker_to_event(event_id: int,
                                 hacker_id: int,
                                 db: Session = Depends(get_db),
                                 token: str = Depends(JWTBearer())):
    """
        Accept a hacker to an event
        """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.accept_hacker_to_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/acceptgroup/{group_id}")
async def accept_group_to_event(event_id: int,
                                group_id: int,
                                db: Session = Depends(get_db),
                                token: str = Depends(JWTBearer())):
    """
            Accept a group to an event
            """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    group = await hackergroup_service.get_hacker_group(group_id, db)
    if group is None:
        raise NotFoundException("Group not found")
    return await eventmanagment_service.accept_group_to_event(
        event, group, db, get_data_from_token(token))


@router.put("/{event_id}/reject/{hacker_id}")
async def reject_hacker_from_event(event_id: int,
                                   hacker_id: int,
                                   db: Session = Depends(get_db),
                                   token: str = Depends(JWTBearer())):
    """
        Reject a hacker from an event
        """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.reject_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/rejectgroup/{group_id}")
async def reject_group_from_event(event_id: int,
                                  group_id: int,
                                  db: Session = Depends(get_db),
                                  token: str = Depends(JWTBearer())):
    """
          Reject a group from an event
          """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    group = await hackergroup_service.get_hacker_group(group_id, db)
    if group is None:
        raise NotFoundException("Group not found")
    return await eventmanagment_service.reject_group_from_event(
        event, group, db, get_data_from_token(token))


@router.get("/{event_id}/pending")
async def get_pending_hackers(event_id: int,
                              db: Session = Depends(get_db),
                              token: str = Depends(JWTBearer())):
    """
    Get the pending hackers of an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return {
        'size': len(event.registered_hackers),
        'hackers': event.registered_hackers
    }


@router.get("/{event_id}/pendinggruped")
async def get_pending_hackers_gruped(event_id: int,
                                     db: Session = Depends(get_db),
                                     token: str = Depends(JWTBearer())):
    """
        Get the pending hackers of an event
        """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_pending_hackers_gruped(
        event, db, get_data_from_token(token))


@router.get("/{event_id}/rejected")
async def get_rejected_hackers(event_id: int,
                               db: Session = Depends(get_db),
                               token: str = Depends(JWTBearer())):
    """
        Get the rejected hackers of an event
        """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return {
        'size': len(event.rejected_hackers),
        'hackers': event.rejected_hackers
    }


@router.get("/{event_id}/status")
async def get_event_status(event_id: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    """
    Get the status of an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_event_status(event, db)


@router.put("/{event_id}/eat/{meal_id}/{hacker_id}")
async def eat(event_id: int,
              meal_id: int,
              hacker_id: int,
              db: Session = Depends(get_db),
              token: str = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker(hacker_id, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    meal = [meal for meal in event.meals if meal.id == meal_id][0]
    return await eventmanagment_service.eat(event, meal, hacker, db,
                                            get_data_from_token(token))


@router.get("/get_hackeps")
async def get_hackeps(year: int = None,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    """
    Get the hackeps
    """
    return await eventmanagment_service.get_hackeps(db,
                                                    get_data_from_token(token))
