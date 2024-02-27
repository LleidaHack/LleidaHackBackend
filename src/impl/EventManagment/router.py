import time
from typing import List
from fastapi import BackgroundTasks, Depends, Response, APIRouter
from sqlalchemy.orm import Session

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

from src.utils.service_utils import subtract_lists
from src.utils.Token import BaseToken
from src.utils.JWTBearer import JWTBearer
from src.utils.security import get_data_from_token
from src.utils.database import get_db
from src.utils.Configuration import Configuration

from src.impl.Event.schema import HackerEventRegistration as EventRegistrationSchema
from src.impl.Event.schema import HackerEventRegistrationUpdate as EventRegistrationUpdateSchema

from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.HackerGroup.service import HackerGroupService
import src.impl.EventManagment.service as eventmanagment_service
from src.impl.Hacker.service import HackerService
import services.mail as mail_service

from src.impl.Hacker.schema import HackerGet as HackerGetSchema

router = APIRouter(
    prefix="/eventmanagment",
    tags=["EventManagment"],
)

hacker_service = HackerService()
event_service = EventService()
hacker_group_service = HackerGroupService()


@router.put("/{event_id}/register/{hacker_id}")
def register_hacker_to_event(event_id: int,
                             hacker_id: str,
                             registration: EventRegistrationSchema,
                             db: Session = Depends(get_db),
                             token: BaseToken = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = event_service.get_event(event_id, db)
    hacker = hacker_service.get_hacker(hacker_id, db,
                                       get_data_from_token(token))
    return eventmanagment_service.register_hacker_to_event(
        registration, event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/unregister/{hacker_id}")
def unregister_hacker_from_event(event_id: int,
                                 hacker_id: int,
                                 db: Session = Depends(get_db),
                                 token: BaseToken = Depends(JWTBearer())):
    """
    Unregister a hacker from an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker(hacker_id, db,
                                       get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return eventmanagment_service.unregister_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.get("/confirm-assistance")
def confirm_assistance(token: str, db: Session = Depends(get_db)):
    """
    Confirm assistance of a hacker to an event
    """
    eventmanagment_service.confirm_assistance(token, db)
    #redirect to Configuration.get('OTHERS', 'FRONT_URL')
    return Response(
        status_code=303,
        headers={"Location": Configuration.get('OTHERS', 'FRONT_URL')})


@router.put("/{event_id}/participate/{hacker_code}")
def participate_hacker_to_event(event_id: int,
                                hacker_code: str,
                                db: Session = Depends(get_db),
                                token: BaseToken = Depends(JWTBearer())):
    """
    Participate a hacker to an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker_by_code(hacker_code, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    m, reg = eventmanagment_service.participate_hacker_to_event(
        event, hacker, db, get_data_from_token(token))
    return {
        'success': True,
        'event_id': event.id,
        'hacker_id': hacker.id,
        'hacker_name': hacker.name,
        'hacker_shirt_size': reg.shirt_size,
        'food_restrictions': reg.food_restrictions,
        'message': m,
    }


@router.put("/{event_id}/unparticipate/{hacker_id}")
def unparticipate_hacker_from_event(event_id: int,
                                    hacker_id: int,
                                    db: Session = Depends(get_db),
                                    token: BaseToken = Depends(JWTBearer())):
    """
    Unparticipate a hacker from an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker(hacker_id, db,
                                       get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    eventmanagment_service.unparticipate_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/accept/{hacker_id}")
def accept_hacker_to_event(event_id: int,
                           hacker_id: int,
                           db: Session = Depends(get_db),
                           token: BaseToken = Depends(JWTBearer())):
    """
        Accept a hacker to an event
        """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker(hacker_id, db,
                                       get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return eventmanagment_service.accept_hacker_to_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/unaccept/{hacker_email}")
def unaccept_hacker_from_event_by_email(event_id: int,
                                        hacker_email: str,
                                        db: Session = Depends(get_db),
                                        token: BaseToken = Depends(
                                            JWTBearer())):
    """
    Unaccept a hacker from an event by email
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker_by_email(hacker_email, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return eventmanagment_service.unaccept_hacker_to_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/acceptgroup/{group_id}")
def accept_group_to_event(event_id: int,
                          group_id: int,
                          db: Session = Depends(get_db),
                          token: BaseToken = Depends(JWTBearer())):
    """
            Accept a group to an event
            """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    group = hackergroup_service.get_hacker_group(group_id, db)
    if group is None:
        raise NotFoundException("Group not found")
    return eventmanagment_service.accept_group_to_event(
        event, group, db, get_data_from_token(token))


@router.put("/{event_id}/reject/{hacker_id}")
def reject_hacker_from_event(event_id: int,
                             hacker_id: int,
                             db: Session = Depends(get_db),
                             token: BaseToken = Depends(JWTBearer())):
    """
        Reject a hacker from an event
        """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker(hacker_id, db,
                                       get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return eventmanagment_service.reject_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/rejectgroup/{group_id}")
def reject_group_from_event(event_id: int,
                            group_id: int,
                            db: Session = Depends(get_db),
                            token: BaseToken = Depends(JWTBearer())):
    """
          Reject a group from an event
          """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    group = hackergroup_service.get_hacker_group(group_id, db)
    if group is None:
        raise NotFoundException("Group not found")
    return eventmanagment_service.reject_group_from_event(
        event, group, db, get_data_from_token(token))


@router.get("/{event_id}/pending")
def get_pending_hackers(event_id: int,
                        db: Session = Depends(get_db),
                        token: BaseToken = Depends(JWTBearer())):
    """
    Get the pending hackers of an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return {
        'size': len(event.registered_hackers),
        'hackers': subtract_lists(event.registered_hackers,
                                  event.accepted_hackers)
    }


@router.get("/{event_id}/pendinggruped")
def get_pending_hackers_gruped(event_id: int,
                               db: Session = Depends(get_db),
                               token: BaseToken = Depends(JWTBearer())):
    """
        Get the pending hackers of an event
        """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.get_pending_hackers_gruped(
        event, db, get_data_from_token(token))


@router.get("/{event_id}/rejected")
def get_rejected_hackers(event_id: int,
                         db: Session = Depends(get_db),
                         token: BaseToken = Depends(JWTBearer())):
    """
        Get the rejected hackers of an event
        """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return {
        'size': len(event.rejected_hackers),
        'hackers': event.rejected_hackers
    }


@router.get("/{event_id}/status")
def get_event_status(event_id: int, db: Session = Depends(get_db)):
    """
    Get the status of an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.get_event_status(event, db)


@router.get("/{event_id}/food_restrictions")
def get_food_restrictions(event_id: int, db: Session = Depends(get_db)):
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.get_food_restrictions(event, db)


@router.put("/{event_id}/eat/{meal_id}/{hacker_code}")
def eat(event_id: int,
        meal_id: int,
        hacker_code: str,
        db: Session = Depends(get_db),
        token: BaseToken = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = hacker_service.get_hacker_by_code(hacker_code, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    meal = [meal for meal in event.meals if meal.id == meal_id][0]
    return eventmanagment_service.eat(event, meal, hacker, db,
                                      get_data_from_token(token))


# def test(lst, background_tasks: BackgroundTasks):
#     for u in lst:
#         mail_service.send_reminder_email(u)
#         time.sleep(10)


# background_tasks.add_task(mail_service.send_reminder_email, u)
@router.post("/{event_id}/send_remember")
def send_remember(
    event_id: int,
    # background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: BaseToken = Depends(JWTBearer())):
    """
    Send a remember notification to all attendees of an event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    all = hacker_service.get_all(db)
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    users = subtract_lists(all, event.registered_hackers)
    return mail_service.send_all_reminder_mails(users)


@router.post("/{event_id}/send_dailyhack")
def send_dailyhack(event_id: int,
                   background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db),
                   token: BaseToken = Depends(JWTBearer())):
    """
    Send a daily hack notification to all attendees of an event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return mail_service.send_all_dailyhack_mails(event.registered_hackers)


@router.get("/{event_id}/get_sizes")
def get_sizes(event_id: int, db: Session = Depends(get_db)):
    """
    Get the sizes of all the shirts of the registered hackers
    """
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.get_sizes(event, db)


@router.get("/{event_id}/get_unregistered_hackers",
            response_model=List[HackerGetSchema])
def get_unregistered_hackers(event_id: int,
                             db: Session = Depends(get_db),
                             token: BaseToken = Depends(JWTBearer())):
    """
    Get the hackers who are not registered for the event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.get_hackers_unregistered(event, db)


@router.get("/{event_id}/count_unregistered_hackers")
def count_unregistered_hackers(event_id: int,
                               db: Session = Depends(get_db),
                               token: BaseToken = Depends(JWTBearer())):
    """
    Get the count of hackers who are not registered for the event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return eventmanagment_service.count_hackers_unregistered(event, db)
