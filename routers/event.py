from database import get_db
from security import oauth_schema, get_data_from_token

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import check_permissions

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Company import Company as ModelCompany
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup

import services.event as event_service

router = APIRouter(
    prefix="/event",
    tags=["Event"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_events(db: Session = Depends(get_db),
                     tokem: str = Depends(oauth_schema)):
    return await event_service.get_all(db)


@router.get("/{id}")
async def get_event(id: int,
                    db: Session = Depends(get_db),
                    tokem: str = Depends(oauth_schema)):
    return await event_service.get_event(id, db)


@router.post("/")
async def create_event(event: SchemaEvent,
                       db: Session = Depends(get_db),
                       tokem: str = Depends(oauth_schema)):
    await check_permissions(tokem, ["admin"])
    new_event = await event_service.add_event(event, db,
                                              get_data_from_token(tokem))
    return {'success': True, 'event_id': new_event.id}


@router.post("/{id}/logo/{logo_id}")
async def set_event_logo(id: int,
                         logo_id: str,
                         db: Session = Depends(get_db),
                         tokem: str = Depends(oauth_schema)):
    event = await event_service.set_event_logo(id, logo_id, db,
                                               get_data_from_token(tokem))
    return {'success': True, 'event_id': event.id}


@router.put("/{id}")
async def update_event(id: int,
                       event: SchemaEvent,
                       db: Session = Depends(get_db),
                       tokem: str = Depends(oauth_schema)):
    new_event = await event_service.update_event(id, event, db,
                                                 get_data_from_token(tokem))
    return {'success': True, 'event_id': new_event.id}


@router.delete("/{id}")
async def delete_event(id: int,
                       db: Session = Depends(get_db),
                       tokem: str = Depends(oauth_schema)):
    event = await event_service.delete_event(id, db,
                                             get_data_from_token(tokem))
    return {'success': True, 'event_id': event.id}


@router.get("/{id}/participants")
async def get_event_participants(id: int,
                                 db: Session = Depends(get_db),
                                 tokem: str = Depends(oauth_schema)):
    return await event_service.get_event_participants(
        id, db, get_data_from_token(tokem))


@router.get("/{id}/sponsors")
async def get_event_sponsors(id: int,
                             db: Session = Depends(get_db),
                             tokem: str = Depends(oauth_schema)):
    return await event_service.get_event_sponsors(id, db,
                                                  get_data_from_token(tokem))


@router.get("/{id}/groups")
async def get_event_groups(id: int,
                           db: Session = Depends(get_db),
                           tokem: str = Depends(oauth_schema)):
    event = event_service.get_event_groups(id, db, get_data_from_token(tokem))
    return {'success': True, 'groups': event.groups}


@router.put("/{id}/participants/{hacker_id}")
async def add_event_participant(id: int,
                                hacker_id: int,
                                db: Session = Depends(get_db),
                                tokem: str = Depends(oauth_schema)):
    event = await event_service.add_hacker(id, hacker_id, db,
                                           get_data_from_token(tokem))
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/participants/{hacker_id}")
async def remove_event_participant(id: int,
                                   hacker_id: int,
                                   db: Session = Depends(get_db),
                                   tokem: str = Depends(oauth_schema)):
    event = await event_service.remove_hacker(id, hacker_id, db,
                                              get_data_from_token(tokem))
    return {'success': True, 'event_id': event.id}


@router.put("/{id}/sponsors/{company_id}")
async def add_event_sponsor(id: int,
                            company_id: int,
                            db: Session = Depends(get_db),
                            tokem: str = Depends(oauth_schema)):
    event = await event_service.add_company(id, company_id, db,
                                            get_data_from_token(tokem))
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/sponsors/{company_id}")
async def remove_event_sponsor(id: int,
                               company_id: int,
                               db: Session = Depends(get_db),
                               tokem: str = Depends(oauth_schema)):
    event = await event_service.remove_company(id, company_id, db)
    return {'success': True, 'event_id': event.id}


@router.put("/{id}/group/{group_id}")
async def add_event_group(id: int,
                          group_id: int,
                          db: Session = Depends(get_db),
                          tokem: str = Depends(oauth_schema)):
    event = await event_service.add_group(id, group_id, db)
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/group/{group_id}")
async def remove_event_group(id: int,
                             group_id: int,
                             db: Session = Depends(get_db),
                             tokem: str = Depends(oauth_schema)):
    event = await event_service.remove_group(id, group_id, db)
    return {'success': True, 'event_id': event.id}
