from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session
from database import get_db

from security import oauth_schema, get_data_from_token
from models.Event import Event
import services.event as event_service
import services.hacker as hacker_service
import services.eventmanagment as eventmanagment_service

router = APIRouter(
    prefix="/eventmanagment",
    tags=["EventManagment"],
)


@router.put("/{event_id}/register/{hacker_id}")
async def register_hacker_to_event(event_id: int,
                                   hacker_id: int,
                                   db: Session = Depends(get_db),
                                   token: str = Depends(oauth_schema)):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    return await eventmanagment_service.register_hacker_to_event(event, hacker, db,
                                                    get_data_from_token(token))


@router.put("/{event_id}/unregister/{hacker_id}")
async def unregister_hacker_from_event(event_id: int,
                                 hacker_id: int,
                                 db: Session = Depends(get_db),
                                 token: str = Depends(oauth_schema)):
    """
    Unregister a hacker from an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    return await eventmanagment_service.unregister_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/participate/{hacker_id}")
async def participate_hacker_to_event(event_id: int,
                                hacker_id: int,
                                db: Session = Depends(get_db),
                                token: str = Depends(oauth_schema)):
    """
    Participate a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    await eventmanagment_service.participate_hacker_to_event(
        event, hacker, db, get_data_from_token(token))
    return Response(status_code=200)


@router.put("/{event_id}/unparticipate/{hacker_id}")
async def unparticipate_hacker_from_event(event_id: int,
                                    hacker_id: int,
                                    db: Session = Depends(get_db),
                                    token: str = Depends(oauth_schema)):
    """
    Unparticipate a hacker from an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    await eventmanagment_service.unparticipate_hacker_from_event(
        event, hacker, db, get_data_from_token(token))
    return Response(status_code=200)


@router.put("/{event_id}/accept/{hacker_id}")
async def accept_hacker_to_event(event_id: int,
                           hacker_id: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(oauth_schema)):
    """
        Accept a hacker to an event
        """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    await eventmanagment_service.accept_hacker_to_event(event, hacker, db,
                                                  get_data_from_token(token))
    return Response(status_code=200)


@router.put("/{event_id}/reject/{hacker_id}")
async def reject_hacker_from_event(event_id: int,
                             hacker_id: int,
                             db: Session = Depends(get_db),
                             token: str = Depends(oauth_schema)):
    """
        Reject a hacker from an event
        """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    return await eventmanagment_service.reject_hacker_from_event(event, hacker, db,
                                                    get_data_from_token(token))


@router.get("/{event_id}/status")
async def get_event_status(event_id: int,
                     db: Session = Depends(get_db),
                     token: str = Depends(oauth_schema)):
    """
    Get the status of an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        return Response(status_code=404)
    return await eventmanagment_service.get_event_status(event, db)


@router.put("/{event_id}/eat/{meal_id}/{hacker_id}")
async def eat(event_id: int,
        meal_id: int,
        hacker_id: int,
        db: Session = Depends(get_db),
        token: str = Depends(oauth_schema)):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db)
    meal = [meal for meal in event.meals if meal.id == meal_id][0]
    return await eventmanagment_service.eat(event, meal, hacker, db, get_data_from_token(token))
