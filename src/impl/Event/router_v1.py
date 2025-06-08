from datetime import datetime

from fastapi import APIRouter

from src.error.AuthenticationError import AuthenticationError
from src.impl.Company.schema import CompanyGet
from src.impl.Event.schema import (
    EventCreate,
    EventGet,
    EventGetAll,
    EventUpdate,
    HackerEventRegistration,
    HackerEventRegistrationUpdate,
)
from src.impl.Event.service import EventService
from src.impl.Hacker.schema import HackerGet, HackerGetAll
from src.impl.Meal.schema import MealGet
from src.utils.jwt_bearer import jwt_dependency
from src.utils.service_utils import subtract_lists
from src.utils.token import AssistenceToken, BaseToken

# from src.error.NotFoundError import NotFoundError

router = APIRouter(
    prefix='/event',
    tags=['Event'],
)

event_service = EventService()


@router.get('/get_hackeps', response_model=EventGet)
def get_hackeps():
    # get the current year
    year = datetime.now().year
    return event_service.get_hackeps(int(year))


@router.get('/get_hackeps/{year}', response_model=EventGet)
def get_hackeps_by_year(year: str):
    return event_service.get_hackeps(int(year))


@router.get('/all', response_model=list[EventGet])
def get_all(token: BaseToken = jwt_dependency):
    return event_service.get_all()


@router.get('/{event_id}', response_model=EventGetAll | EventGet)
def get(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_event(event_id, token)


@router.post('/')
def create(event: EventCreate, token: BaseToken = jwt_dependency):
    new_event = event_service.add_event(event, token)
    return {'success': True, 'event_id': new_event.id}


@router.put('/{event_id}')
def update(event_id: int, event: EventUpdate, token: BaseToken = jwt_dependency):
    new_event, updated = event_service.update_event(event_id, event, token)
    return {'success': True, 'event_id': new_event.id, 'updated': updated}


@router.delete('/{event_id}')
def delete(event_id: int, token: BaseToken = jwt_dependency):
    event = event_service.delete_event(event_id, token)
    return {'success': True, 'event_id': event.id}


@router.get('/{event_id}/is_registered/{hacker_id}')
def is_registered(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    return event_service.is_registered(event_id, hacker_id, token)


@router.get('/{event_id}/is_accepted/{hacker_id}')
def is_accepted(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    return event_service.is_accepted(event_id, hacker_id, token)


@router.get('/{event_id}/has_confirmed/{hacker_id}')
def has_confirmed(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    return event_service.has_confirmed(event_id, hacker_id, token)


@router.get('/{event_id}/is_participant/{hacker_id}')
def is_participant(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    return event_service.is_participant(event_id, hacker_id, token)


@router.get('/{event_id}/meals', response_model=list[MealGet])
def get_meals(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_event_meals(event_id, token)


@router.get('/{event_id}/participants', response_model=list[HackerGet])
def get_participants(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_event_participants(event_id, token)


@router.get('/{event_id}/sponsors', response_model=list[CompanyGet])
def get_sponsors(event_id: int):
    return event_service.get_event_sponsors(event_id)


@router.get('/{event_id}/groups')
def get_groups(event_id: int, token: BaseToken = jwt_dependency):
    event = event_service.get_event_groups(event_id, token)
    return {'success': True, 'groups': event}


@router.put('/{event_id}/groups/{group_id}')
def add_group(event_id: int, group_id: int, token: BaseToken = jwt_dependency):
    event = event_service.add_hacker_group(event_id, group_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete('/{event_id}/groups/{group_id}')
def remove_group(event_id: int, group_id: int, token: BaseToken = jwt_dependency):
    event = event_service.remove_hacker_group(event_id, group_id, token)
    return {'success': True, 'event_id': event.id}


@router.put('/{event_id}/register/{hacker_id}')
def register_hacker(
    event_id: int,
    hacker_id: int,
    payload: HackerEventRegistration,
    token: BaseToken = jwt_dependency,
):
    event = event_service.add_hacker(event_id, hacker_id, payload, token)
    return {'success': True, 'event_id': event.id, 'user_id': hacker_id}


@router.put('/{event_id}/update-register/{hacker_id}')
def update_hacker_registration(
    event_id: int,
    hacker_id: int,
    payload: HackerEventRegistrationUpdate,
    token: BaseToken = jwt_dependency,
):
    event = event_service.update_register(event_id, hacker_id, payload, token)
    return {'success': True, 'event_id': event.id, 'user_id': hacker_id}


# @router.delete("/{id}/participants/{hacker_id}")
# def remove_event_participant(id: int,
#                                    hacker_id: int,
#                                    ,
#                                    token: BaseToken = jwt_dependency):
#     event = event_service.remove_hacker(id, hacker_id,
#                                               get_data_from_token(token))
#     return {'success': True, 'event_id': event.id}


@router.put('/{event_id}/sponsors/{company_id}')
def add_sponsor(event_id: int, company_id: int, token: BaseToken = jwt_dependency):
    event = event_service.add_company(event_id, company_id, token)
    return {'success': True, 'event_id': event.id}


@router.delete('/{event_id}/sponsors/{company_id}')
def remove_sponsor(event_id: int, company_id: int, token: BaseToken = jwt_dependency):
    event = event_service.remove_company(event_id, company_id, token)
    return {'success': True, 'event_id': event.id}


@router.get('/{event_id}/get_approved_hackers', response_model=list[HackerGetAll])
def get_accepted_hackers(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_accepted_hackers(event_id, token)


@router.get('/{event_id}/get_approved_hackers_mails', response_model=list[str])
def get_accepted_hackers_mails(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_accepted_hackers_mails(event_id, token)


@router.get('/{event_id}/get_sizes')
def get_sizes(event_id: int):
    """
    Get the sizes of all the shirts of the registered hackers
    """
    return event_service.get_sizes(event_id)


@router.get('/{event_id}/get_unregistered_hackers', response_model=list[HackerGet])
def get_unregistered_hackers(event_id: int, token: BaseToken = jwt_dependency):
    """
    Get the hackers who are not registered for the event
    """
    if not token.is_admin:
        raise AuthenticationError('Not authorized')
    return event_service.get_hackers_unregistered(event_id)


@router.get('/{event_id}/count_unregistered_hackers/', response_model=int)
def count_unregistered_hackers(event_id: int, token: BaseToken = jwt_dependency):
    """
    Get the count of hackers who are not registered for the event
    """
    if not token.is_admin:
        raise AuthenticationError('Not authorized')
    return event_service.count_hackers_unregistered(event_id)


@router.get('/confirm_assistance/')
def confirm_assistance(token: AssistenceToken = jwt_dependency):
    """
    Confirm assistance of a hacker to an event
    """
    event_service.confirm_assistance(token)
    # redirect to Configuration.get('OTHERS', 'FRONT_URL')
    return {'success': True}


@router.get('/force/confirm_assistance/{event_id}/{user_id}')
def force_confirm_assistance(
    event_id: int, user_id: int, token: BaseToken = jwt_dependency
):
    """
    Confirm assistance of a hacker to an event
    """
    return event_service.force_confirm_assistance(user_id, event_id, token)


@router.put('/{event_id}/participate/{hacker_code}')
def participate_hacker(
    event_id: int, hacker_code: str, token: BaseToken = jwt_dependency
):
    """
    Participate a hacker to an event
    """
    return event_service.participate_hacker(event_id, hacker_code, token)


@router.put('/{event_id}/unparticipate/{hacker_code}')
def unparticipate_hacker(
    event_id: int, hacker_code: str, token: BaseToken = jwt_dependency
):
    """
    Unparticipate a hacker from an event
    """
    event_service.unparticipate_hacker(event_id, hacker_code, token)
    return {'success': True}


@router.put('/{event_id}/accept/{hacker_id}')
def accept_hacker(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    """
    Accept a hacker to an event
    """
    return event_service.accept_hacker(event_id, hacker_id, token)


@router.put('/{event_id}/unaccept/{hacker_id}')
def unaccept_hacker(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    """
    Unaccept a hacker from an event
    """
    return event_service.unaccept_hacker(event_id, hacker_id, token)


@router.put('/{event_id}/reject/{hacker_id}')
def reject_hacker(event_id: int, hacker_id: int, token: BaseToken = jwt_dependency):
    """
    Reject a hacker from an event
    """
    return event_service.reject_hacker(event_id, hacker_id, token)


@router.put('/{event_id}/acceptgroup/{group_id}')
def accept_group(event_id: int, group_id: int, token: BaseToken = jwt_dependency):
    return event_service.accept_group(event_id, group_id, token)


@router.put('/{event_id}/rejectgroup/{group_id}')
def reject_group(event_id: int, group_id: int, token: BaseToken = jwt_dependency):
    """
    Reject a group from an event
    """
    return event_service.reject_group(event_id, group_id, token)


@router.get('/{event_id}/pending')
def get_pending_hackers(event_id: int, token: BaseToken = jwt_dependency):
    """
    Get the pending hackers of an event
    """
    if not token.is_admin:
        raise AuthenticationError("You don't have permissions")
    event = event_service.get_by_id(event_id)
    return {
        'size': len(event.registered_hackers),
        'hackers': subtract_lists(event.registered_hackers, event.accepted_hackers),
    }


@router.get('/{event_id}/rejected')
def get_rejected_hackers(event_id: int, token: BaseToken = jwt_dependency):
    """
    Get the rejected hackers of an event
    """
    if not token.is_admin:
        raise AuthenticationError("You don't have permissions")
    event = event_service.get_by_id(event_id)
    return {'size': len(event.rejected_hackers), 'hackers': event.rejected_hackers}


@router.get('/{event_id}/status')
def get_status(event_id: int):
    """
    Get the status of an event
    """
    return event_service.get_status(event_id)


@router.get('/{event_id}/statistics')
def get_statistics(event_id: int):
    """
    Get the status of an event
    """
    return event_service.get_statistics(event_id)


@router.get('/{event_id}/food_restrictions')
def get_food_restrictions(event_id: int):
    return event_service.get_food_restrictions(event_id)


@router.get('/{event_id}/credits')
def get_credits(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_credits(event_id, token)


@router.get('/{event_id}/pendinggruped')
def get_pending_hackers_gruped(event_id: int, token: BaseToken = jwt_dependency):
    return event_service.get_pending_hackers_gruped(event_id, token)


@router.get('/{event_id}/resend-accepted-mails')
def resend_accept_mails(event_id: int, token: BaseToken = jwt_dependency):
    event_service.resend_mails(event_id, token)
    return {'success': True}


@router.get('/{event_id}/resend-accepted-mail/{hacker_id}/')
def resend_accept_mail(
    event_id: int, hacker_id: int, token: BaseToken = jwt_dependency
):
    event_service.resend_mail(event_id, hacker_id, token)
    return {'success': True}


@router.get('/{event_id}/send_slack_mail/')
def send_slack_mail(event_id: int, token: BaseToken = jwt_dependency):
    event_service.send_slack_mail(event_id, token)
    return {'success': True}


# @router.post("/{event_id}/send_remember")
# def send_remember(
#     event_id: int,
#     # background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db),
#     token: BaseToken = jwt_dependency):
#     """
#     Send a remember notification to all attendees of an event
#     """
#     data = get_data_from_token(token)
#     if not data.is_admin:
#         raise AuthenticationError("Not authorized")
#     all = hacker_service.get_all(db)
#     event = event_service.get_event(event_id, db)
#     if event is None:
#         raise NotFoundError("Event not found")
#     users = subtract_lists(all, event.registered_hackers)
#     return mail_service.send_all_reminder_mails(users)
