from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, Response

from src.configuration.Configuration import Configuration
from src.error.AuthenticationException import AuthenticationException
from src.impl.Company.schema import CompanyGet as CompanyGetSchema
from src.impl.Event.schema import EventCreate as EventCreateSchema
from src.impl.Event.schema import EventGet as EventGetSchema
from src.impl.Event.schema import EventGetAll as EventGetAllSchema
from src.impl.Event.schema import EventUpdate as EventUpdateSchema
from src.impl.Event.service import EventService
from src.impl.Hacker.schema import HackerGet as HackerGetSchema
from src.impl.HackerGroup.schema import HackerGroupGet as HackerGroupGetSchema
from src.impl.Meal.schema import MealGet as MealGetSchema
from src.utils.JWTBearer import JWTBearer
from src.utils.service_utils import subtract_lists
from src.utils.Token import AssistenceToken, BaseToken

# from src.error.NotFoundException import NotFoundException

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
def get_all(token: BaseToken = Depends(JWTBearer())):
    return event_service.get_all()


@router.get("/{id}", response_model=Union[EventGetAllSchema, EventGetSchema])
def get(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event(id, token)


@router.post("/")
def create(event: EventCreateSchema, token: BaseToken = Depends(JWTBearer())):
    new_event = event_service.add_event(event, token)
    return {'success': True, 'event_id': new_event.id}


@router.put("/{id}")
def update(id: int,
           event: EventUpdateSchema,
           token: BaseToken = Depends(JWTBearer())):
    new_event, updated = event_service.update_event(id, event, token)
    return {'success': True, 'event_id': new_event.id, 'updated': updated}


@router.delete("/{id}")
def delete(id: int, token: BaseToken = Depends(JWTBearer())):
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
def get_meals(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event_meals(id, token)


@router.get("/{id}/participants", response_model=List[HackerGetSchema])
def get_participants(id: int, token: BaseToken = Depends(JWTBearer())):
    return event_service.get_event_participants(id, token)


@router.get("/{id}/sponsors", response_model=List[CompanyGetSchema])
def get_sponsors(id: int):
    return event_service.get_event_sponsors(id)


@router.get("/{id}/groups", response_model=List[HackerGroupGetSchema])
def get_groups(id: int, token: BaseToken = Depends(JWTBearer())):
    event = event_service.get_event_groups(id, token)
    return {'success': True, 'groups': event}


@router.put("/{id}/groups/{group_id}")
def add_group(id: int, group_id: int, token: BaseToken = Depends(JWTBearer())):
    event = event_service.add_hacker_group(id, group_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/groups/{group_id}")
def remove_group(id: int,
                 group_id: int,
                 token: BaseToken = Depends(JWTBearer())):
    event = event_service.remove_hacker_group(id, group_id, token)
    return {'success': True, 'event_id': event.id}


@router.put("/{id}/register/{hacker_id}")
def register_hacker(id: int,
                    hacker_id: int,
                    token: BaseToken = Depends(JWTBearer())):
    event = event_service.add_hacker(id, hacker_id, token)
    return {'success': True, 'event_id': event.id, 'user_id': hacker_id}


# @router.delete("/{id}/participants/{hacker_id}")
# def remove_event_participant(id: int,
#                                    hacker_id: int,
#                                    ,
#                                    token: BaseToken = Depends(JWTBearer())):
#     event = event_service.remove_hacker(id, hacker_id,
#                                               get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}


@router.put("/{id}/sponsors/{company_id}")
def add_sponsor(id: int,
                company_id: int,
                token: BaseToken = Depends(JWTBearer())):
    event = event_service.add_company(id, company_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete("/{id}/sponsors/{company_id}")
def remove_sponsor(id: int,
                   company_id: int,
                   token: BaseToken = Depends(JWTBearer())):
    event = event_service.remove_company(id, company_id, token)
    return {'success': True, 'event_id': event.id}


@router.get("/{eventId}/get_approved_hackers", response_model=List[HackerGetSchema])
def get_accepted_hackers(eventId: int,
                         token: BaseToken = Depends(JWTBearer())):
    return event_service.get_accepted_hackers(eventId, token)


@router.get("/{eventId}/get_approved_hackers_mails", response_model=List[str])
def get_accepted_hackers_mails(eventId: int,
                               token: BaseToken = Depends(JWTBearer())):
    return event_service.get_accepted_hackers_mails(eventId, token)


@router.get("/{event_id}/get_sizes")
def get_sizes(event_id: int):
    """
    Get the sizes of all the shirts of the registered hackers
    """
    return event_service.get_sizes(event_id)


@router.get("/{event_id}/get_unregistered_hackers",
            response_model=List[HackerGetSchema])
def get_unregistered_hackers(event_id: int,
                             token: BaseToken = Depends(JWTBearer())):
    """
    Get the hackers who are not registered for the event
    """
    if not token.is_admin:
        raise AuthenticationException("Not authorized")
    return event_service.get_hackers_unregistered(event_id)


@router.get("/{event_id}/count_unregistered_hackers", response_model=int)
def count_unregistered_hackers(event_id: int,
                               token: BaseToken = Depends(JWTBearer())):
    """
    Get the count of hackers who are not registered for the event
    """
    if not token.is_admin:
        raise AuthenticationException("Not authorized")
    return event_service.count_hackers_unregistered(event_id)


@router.get("/confirm-assistance")
def confirm_assistance(token: AssistenceToken = Depends(JWTBearer())):
    """
    Confirm assistance of a hacker to an event
    """
    event_service.confirm_assistance(token)
    #redirect to Configuration.get('OTHERS', 'FRONT_URL')
    return Response(
        status_code=303,
        headers={"Location": Configuration.front_url})


@router.get("/force-confirm-assistance/{event_id}/{user_id}")
def force_confirm_assistance(event_id: int,
                             user_id: int,
                             token: BaseToken = Depends(JWTBearer())):
    """
    Confirm assistance of a hacker to an event
    """
    return event_service.force_confirm_assistance(user_id, event_id, token)


@router.put("/{event_id}/participate/{hacker_code}")
def participate_hacker(event_id: int,
                       hacker_code: str,
                       token: BaseToken = Depends(JWTBearer())):
    """
    Participate a hacker to an event
    """
    return event_service.participate_hacker(event_id, hacker_code, token)


@router.put("/{event_id}/unparticipate/{hacker_code}")
def unparticipate_hacker(event_id: int,
                         hacker_code: str,
                         token: BaseToken = Depends(JWTBearer())):
    """
    Unparticipate a hacker from an event
    """
    event_service.unparticipate_hacker(event_id, hacker_code, token)
    return {'success': True}


@router.put("/{event_id}/accept/{hacker_id}")
def accept_hacker(event_id: int,
                  hacker_id: int,
                  token: BaseToken = Depends(JWTBearer())):
    """
        Accept a hacker to an event
        """
    return event_service.accept_hacker(event_id, hacker_id, token)


@router.put("/{event_id}/reject/{hacker_id}")
def reject_hacker(event_id: int,
                  hacker_id: int,
                  token: BaseToken = Depends(JWTBearer())):
    """
        Reject a hacker from an event
    """
    return event_service.reject_hacker(event_id, hacker_id, token)


@router.put("/{event_id}/acceptgroup/{group_id}")
def accept_group(event_id: int,
                 group_id: int,
                 token: BaseToken = Depends(JWTBearer())):
    return event_service.accept_group(event_id, group_id, token)


@router.put("/{event_id}/rejectgroup/{group_id}")
def reject_group(event_id: int,
                 group_id: int,
                 token: BaseToken = Depends(JWTBearer())):
    """
          Reject a group from an event
    """
    return event_service.reject_group(event_id, group_id, token)


@router.get("/{event_id}/pending")
def get_pending_hackers(event_id: int,
                        token: BaseToken = Depends(JWTBearer())):
    """
    Get the pending hackers of an event
    """
    if token.is_admin:
        raise AuthenticationException("You don't have permissions")
    event = event_service.get_by_id(event_id)
    return {
        'size': len(event.registered_hackers),
        'hackers': subtract_lists(event.registered_hackers,
                                  event.accepted_hackers)
    }


@router.get("/{event_id}/rejected")
def get_rejected_hackers(event_id: int,
                         token: BaseToken = Depends(JWTBearer())):
    """
        Get the rejected hackers of an event
        """
    if token.is_admin:
        raise AuthenticationException("You don't have permissions")
    event = event_service.get_by_id(event_id)
    return {
        'size': len(event.rejected_hackers),
        'hackers': event.rejected_hackers
    }


@router.get("/{event_id}/status")
def get_status(event_id: int):
    """
    Get the status of an event
    """
    return event_service.get_status(event_id)


@router.get("/{event_id}/food_restrictions")
def get_food_restrictions(event_id: int):
    return event_service.get_food_restrictions(event_id)


@router.get("/{event_id}/pendinggruped")
def get_pending_hackers_gruped(event_id: int,
                               token: BaseToken = Depends(JWTBearer())):
    return event_service.get_pending_hackers_gruped(event_id, token)


# @router.post("/{event_id}/send_remember")
# def send_remember(
#     event_id: int,
#     # background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     token: BaseToken = Depends(JWTBearer())):
#     """
#     Send a remember notification to all attendees of an event
#     """
#     data = get_data_from_token(token)
#     if not data.is_admin:
#         raise AuthenticationException("Not authorized")
#     all = hacker_service.get_all(db)
#     event = event_service.get_event(event_id, db)
#     if event is None:
#         raise NotFoundException("Event not found")
#     users = subtract_lists(all, event.registered_hackers)
#     return mail_service.send_all_reminder_mails(users)
