from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Union

from src.utils.Token import BaseToken
from src.utils.JWTBearer import JWTBearer

from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.Event.schema import EventGetAll as EventGetAllSchema
from src.impl.Event.schema import EventCreate as EventCreateSchema
from src.impl.Event.schema import EventUpdate as EventUpdateSchema
from src.impl.Meal.schema import MealGet as MealGetSchema
from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema
from src.impl.Company.schema import CompanyGet as CompanyGetSchema

from src.impl.Event.service import EventService

router = APIRouter(
    prefix="/event",
    tags=["Event"],
)

event_service = EventService()


@router.get("/get_hackeps", response_model=EventGetSchema)
def get_hackeps():
    #get the current year
    year = datetime.now().year
    return event_service.get_hackeps(int(year))


@router.get("/all", response_model=List[EventGetSchema])
def get_events(token: BaseToken = Depends(JWTBearer())):
    return event_service.get_all()


@router.get("/{id}", response_model=Union[EventGetAllSchema, EventGetSchema])
def get_event(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event(id, token)


@router.post("/")
def create_event(event: EventCreateSchema,
                 token: BaseToken = Depends(JWTBearer())):
    new_event = event_service.add_event(event, token)
    return {'success': True, 'event_id': new_event.id}


@router.put("/{id}")
def update_event(id: int,
                 event: EventUpdateSchema,
                 token: BaseToken = Depends(JWTBearer())):
    new_event, updated = event_service.update_event(id, event,token)
    return {'success': True, 'event_id': new_event.id, 'updated': updated}


@router.delete("/{id}")
def delete_event(id: int, token: BaseToken = Depends(JWTBearer())):
    event = event_service.delete_event(id, token)
    return {'success': True, 'event_id': event.id}


@router.get("/{id}/is_registered/{hacker_id}")
def is_registered(id: int,
                  hacker_id: int,
                  token: BaseToken = Depends(JWTBearer())):
    return event_service.is_registered(id, hacker_id, token)


@router.get("/{id}/is_accepted/{hacker_id}")
def is_accepted(id: int,
                hacker_id: int,
                token: BaseToken = Depends(JWTBearer())):
    return event_service.is_accepted(id, hacker_id, token)


@router.get("/{id}/meals", response_model=List[MealGetSchema])
def get_event_meals(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event_meals(id, token)


@router.get("/{id}/participants", response_model=List[HackerGetSchema])
def get_event_participants(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event_participants(id, token)


@router.get("/{id}/sponsors", response_model=List[CompanyGetSchema])
def get_event_sponsors(id: int):
    return event_service.get_event_sponsors(id)


@router.get("/{id}/groups", response_model=List[HackerGroupGetSchema])
def get_event_groups(id: int, token: BaseToken = Depends(JWTBearer())):
    event = event_service.get_event_groups(id, token)
    return {'success': True, 'groups': event}


@router.put("/{id}/groups/{group_id}")
def add_event_group(id: int,
                    group_id: int,
                    token: BaseToken = Depends(JWTBearer())):
    event = event_service.add_hacker_group(id, group_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/groups/{group_id}")
def remove_event_group(id: int,
                       group_id: int,
                       token: BaseToken = Depends(JWTBearer())):
    event = event_service.remove_hacker_group(id, group_id, token)
    return {'success': True, 'event_id': event.id}


# @router.put("/{id}/participants/{hacker_id}")
# def add_event_participant(id: int,
#                                 hacker_id: int,
#                                 ,
#                                 token: BaseToken = Depends(JWTBearer())):
#     event = event_service.add_hacker(id, hacker_id,
#                                            get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}

# @router.delete("/{id}/participants/{hacker_id}")
# def remove_event_participant(id: int,
#                                    hacker_id: int,
#                                    ,
#                                    token: BaseToken = Depends(JWTBearer())):
#     event = event_service.remove_hacker(id, hacker_id,
#                                               get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}


@router.put("/{id}/sponsors/{company_id}")
def add_event_sponsor(id: int,
                      company_id: int,
                      token: BaseToken = Depends(JWTBearer())):
    event = event_service.add_company(id, company_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/sponsors/{company_id}")
def remove_event_sponsor(id: int,
                         company_id: int,
                         token: BaseToken = Depends(JWTBearer())):
    event = event_service.remove_company(id, company_id, token)
    return {'success': True, 'event_id': event.id}


# @router.get("/{eventId}/get_hacker_group/{hackerId}")
# def get_hacker_group(eventId: int,
#                            hackerId: int,
#                            ,
#                            token: BaseToken = Depends(JWTBearer())):
#     return event_service.get_hacker_group(eventId, hackerId,
#                                                 get_data_from_token(token))


@router.get("/{eventId}/get_approved_hackers",
            response_model=List[HackerGetSchema])
def get_accepted_hackers(eventId: int,
                         token: BaseToken = Depends(JWTBearer())):
    return event_service.get_accepted_hackers(eventId, token)


@router.get("/{eventId}/get_approved_hackers_mails")
def get_accepted_hackers_mails(eventId: int,
                               token: BaseToken = Depends(JWTBearer())):
    return event_service.get_accepted_hackers_mails(eventId, token)
