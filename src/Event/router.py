from datetime import datetime
from database import get_db
from security import get_data_from_token

from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter

from src.Event.Event import Event as SchemaEvent
from src.Event.Event import EventUpdate as SchemaEventUpdate

import src.Event.service as event_service

from utils.auth_bearer import JWTBearer

router = APIRouter(
    prefix="/event",
    tags=["Event"],
)


@router.get("/get_hackeps")
def get_hackeps(db: Session = Depends(get_db)):
    #get the current year
    year = datetime.now().year
    return event_service.get_hackeps(int(year), db)


@router.get("/all")
def get_events(db: Session = Depends(get_db),
                     token: str = Depends(JWTBearer())):
    return event_service.get_all(db)


@router.get("/{id}")
def get_event(id: int,
                    db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return event_service.get_event(id, db)


@router.post("/")
def create_event(event: SchemaEvent,
                       db: Session = Depends(get_db),
                       token: str = Depends(JWTBearer())):
    new_event = event_service.add_event(event, db,
                                              get_data_from_token(token))
    return {'success': True, 'event_id': new_event.id}


@router.put("/{id}")
def update_event(id: int,
                       event: SchemaEventUpdate,
                       db: Session = Depends(get_db),
                       token: str = Depends(JWTBearer())):
    new_event, updated = event_service.update_event(
        id, event, db, get_data_from_token(token))
    return {'success': True, 'event_id': new_event.id, 'updated': updated}


@router.delete("/{id}")
def delete_event(id: int,
                       db: Session = Depends(get_db),
                       token: str = Depends(JWTBearer())):
    event = event_service.delete_event(id, db,
                                             get_data_from_token(token))
    return {'success': True, 'event_id': event.id}


@router.get("/{id}/is_registered/{hacker_id}")
def is_registered(id: int,
                        hacker_id: int,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    return event_service.is_registered(id, hacker_id, db,
                                             get_data_from_token(token))


@router.get("/{id}/is_accepted/{hacker_id}")
def is_accepted(id: int,
                      hacker_id: int,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return event_service.is_accepted(id, hacker_id, db,
                                           get_data_from_token(token))


@router.get("/{id}/meals")
def get_event_meals(id: int,
                          db: Session = Depends(get_db),
                          token: str = Depends(JWTBearer())):
    return event_service.get_event_meals(id, db,
                                               get_data_from_token(token))


@router.get("/{id}/participants")
def get_event_participants(id: int,
                                 db: Session = Depends(get_db),
                                 token: str = Depends(JWTBearer())):
    return event_service.get_event_participants(
        id, db, get_data_from_token(token))


@router.get("/{id}/sponsors")
def get_event_sponsors(id: int, db: Session = Depends(get_db)):
    return event_service.get_event_sponsors(id, db)


@router.get("/{id}/groups")
def get_event_groups(id: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    event = event_service.get_event_groups(id, db,
                                                 get_data_from_token(token))
    return {'success': True, 'groups': event}


@router.put("/{id}/groups/{group_id}")
def add_event_group(id: int,
                          group_id: int,
                          db: Session = Depends(get_db),
                          token: str = Depends(JWTBearer())):
    event = event_service.add_hacker_group(id, group_id, db,
                                                 get_data_from_token(token))
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/groups/{group_id}")
def remove_event_group(id: int,
                             group_id: int,
                             db: Session = Depends(get_db),
                             token: str = Depends(JWTBearer())):
    event = event_service.remove_hacker_group(id, group_id, db,
                                                    get_data_from_token(token))
    return {'success': True, 'event_id': event.id}


# @router.put("/{id}/participants/{hacker_id}")
# def add_event_participant(id: int,
#                                 hacker_id: int,
#                                 db: Session = Depends(get_db),
#                                 token: str = Depends(JWTBearer())):
#     event = event_service.add_hacker(id, hacker_id, db,
#                                            get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}

# @router.delete("/{id}/participants/{hacker_id}")
# def remove_event_participant(id: int,
#                                    hacker_id: int,
#                                    db: Session = Depends(get_db),
#                                    token: str = Depends(JWTBearer())):
#     event = event_service.remove_hacker(id, hacker_id, db,
#                                               get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}


@router.put("/{id}/sponsors/{company_id}")
def add_event_sponsor(id: int,
                            company_id: int,
                            db: Session = Depends(get_db),
                            token: str = Depends(JWTBearer())):
    event = event_service.add_company(id, company_id, db,
                                            get_data_from_token(token))
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/sponsors/{company_id}")
def remove_event_sponsor(id: int,
                               company_id: int,
                               db: Session = Depends(get_db),
                               token: str = Depends(JWTBearer())):
    event = event_service.remove_company(id, company_id, db,
                                               get_data_from_token(token))
    return {'success': True, 'event_id': event.id}


@router.get("/{eventId}/get_hacker_group/{hackerId}")
def get_hacker_group(eventId: int,
                           hackerId: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    return event_service.get_hacker_group(eventId, hackerId, db,
                                                get_data_from_token(token))


@router.get("/{eventId}/get_approved_hackers")
def get_accepted_hackers(eventId: int,
                               db: Session = Depends(get_db),
                               token: str = Depends(JWTBearer())):
    return event_service.get_accepted_hackers(eventId, db,
                                                    get_data_from_token(token))


@router.get("/{eventId}/get_approved_hackers_mails")
def get_accepted_hackers_mails(eventId: int,
                                     db: Session = Depends(get_db),
                                     token: str = Depends(JWTBearer())):
    return event_service.get_accepted_hackers_mails(
        eventId, db, get_data_from_token(token))


# @router.put("/{id}/group/{group_id}")
# def add_event_group(id: int,
#                           group_id: int,
#                           db: Session = Depends(get_db),
#                           token: str = Depends(JWTBearer())):
#     event = event_service.add_group(id, group_id, db)
#     return {'success': True, 'event_id': event.id}

# @router.delete("/{id}/group/{group_id}")
# def remove_event_group(id: int,
#                              group_id: int,
#                              db: Session = Depends(get_db),
#                              token: str = Depends(JWTBearer())):
#     event = event_service.remove_group(id, group_id, db)
#     return {'success': True, 'event_id': event.id}
