

from ast import List
from database import get_db
from security import oauth_schema

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Company import Company as ModelCompany
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup

from routers import eventmanagment

import services.event as event_service

router = APIRouter(
    prefix="/event",
    tags=["Event"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

router.include_router(eventmanagment.router, tags=["EventManagment"])

@router.get("/")
def get_events(db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    return event_service.get_all(db)

@router.get("/{id}")
def get_event(id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    return event_service.get_event(id, db)

@router.post("/")
def create_event(event: SchemaEvent, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    new_event = event_service.add_event(event, db)
    return {'success': True, 'event_id': new_event.id}

@router.put("/{id}")
def update_event(id: int, event: SchemaEvent, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    new_event = event_service.update_event(id, event, db)
    return {'success': True, 'event_id': new_event.id}

@router.delete("/{id}")
def delete_event(id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event= event_service.delete_event(id, db)
    return {'success': True, 'event_id': event.id}

@router.get("/{id}/participants")
def get_event_participants(id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.get_event(id, db)
    return event.participants

@router.get("/{id}/sponsors")
def get_event_sponsors(id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.get_event(id, db)
    return event.sponsors

@router.get("/{id}/groups")
def get_event_groups(id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.get_event(id, db)
    return {'success': True, 'groups': event.groups}

@router.put("/{id}/participants/{hacker_id}")
def add_event_participant(id: int, hacker_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.add_hacker(id, hacker_id, db)
    return {'success': True, 'event_id': event.id}

@router.delete("/{id}/participants/{hacker_id}")
def remove_event_participant(id: int, hacker_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.remove_hacker(id, hacker_id, db)
    return {'success': True, 'event_id': event.id}

@router.put("/{id}/sponsors/{company_id}")
def add_event_sponsor(id: int, company_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.add_company(id, company_id, db)
    return {'success': True, 'event_id': event.id}

@router.delete("/{id}/sponsors/{company_id}")
def remove_event_sponsor(id: int, company_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.remove_company(id, company_id, db)
    return {'success': True, 'event_id': event.id}

@router.put("/{id}/group/{group_id}")
def add_event_group(id: int, group_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.add_group(id, group_id, db)
    return {'success': True, 'event_id': event.id}

@router.delete("/{id}/group/{group_id}")
def remove_event_group(id: int, group_id: int, db: Session = Depends(get_db), tokem: str = Depends(oauth_schema)):
    event = event_service.remove_group(id, group_id, db)
    return {'success': True, 'event_id': event.id}


