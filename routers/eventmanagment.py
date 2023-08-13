from fastapi import Depends, Response, APIRouter
from sqlalchemy.orm import Session
from database import get_db

from models.Event import Event
import services.event as event_service
import services.hacker as hacker_service
import services.eventmanagment as eventacces_service

router = APIRouter(
    prefix="/eventmanagment",
    tags=["EventManagment"],
)


@router.put("/{event_id}/register/{hacker_id}")
def register_hacker_to_event(event_id: int,
                             hacker_id: int,
                             db: Session = Depends(get_db)):
    """
    Register a hacker to an event
    """
    event = event_service.get_event(event_id, db)
    hacker = hacker_service.get_hacker(hacker_id, db)
    event_service.register_hacker_to_event(event, hacker, db)
    return Response(status_code=200)


@router.put("/{event_id}/unregister/{hacker_id}")
def unregister_hacker_from_event(event_id: int,
                                 hacker_id: int,
                                 db: Session = Depends(get_db)):
    """
    Unregister a hacker from an event
    """
    event = event_service.get_event(event_id, db)
    hacker = hacker_service.get_hacker(hacker_id, db)
    event_service.unregister_hacker_from_event(event, hacker, db)
    return Response(status_code=200)


@router.get("/{event_id}/status")
def get_event_status(event_id: int, db: Session = Depends(get_db)):
    """
    Get the status of an event
    """
    event = event_service.get_event(event_id, db)
    return event_service.get_event_status(event, db)


@router.put("/{event_id}/eat/{meal_id}/{hacker_id}")
def eat(event_id: int,
        meal_id: int,
        hacker_id: int,
        db: Session = Depends(get_db)):
    """
    Register a hacker to an event
    """
    event = event_service.get_event(event_id, db)
    hacker = hacker_service.get_hacker(hacker_id, db)
    event_service.eat(event, event.meals[meal_id], hacker, db)
    return Response(status_code=200)
