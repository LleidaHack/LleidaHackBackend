import time
from fastapi import BackgroundTasks, Depends, Response, APIRouter
from sqlalchemy.orm import Session
from config import Configuration
from database import get_db
from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException

from security import get_data_from_token
from schemas.Event import HackerEventRegistration as SchemaEventRegistration
from schemas.Event import HackerEventRegistrationUpdate as SchemaEventRegistrationUpdate
import services.event as event_service
import services.hacker as hacker_service
import services.hackergroup as hackergroup_service
import services.eventmanagment as eventmanagment_service
import services.mail as mail_service
import services.hacker as hacker_service

from utils.auth_bearer import JWTBearer
from utils.service_utils import subtract_lists

router = APIRouter(
    prefix="/eventmanagment",
    tags=["EventManagment"],
)


@router.post("/{event_id}/add_dailyhack/{hacker_id}")
async def add_dailyhack(event_id: int,
                        hacker_id: int,
                        url: str,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    """
    Add a dailyhack to an event
    """
    return await eventmanagment_service.add_dailyhack(
        event_id, hacker_id, url, db, get_data_from_token(token))


@router.put("/{event_id}/update_dailyhack/{hacker_id}")
async def update_dailyhack(event_id: int,
                           hacker_id: int,
                           url: str,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    """
    Update a dailyhack to an event
    """
    return await eventmanagment_service.update_dailyhack(
        event_id, hacker_id, url, db, get_data_from_token(token))


@router.get("/{event_id}/dailyhack/{hacker_id}")
async def get_dailyhack(event_id: int,
                        hacker_id: int,
                        db: Session = Depends(get_db),
                        token: str = Depends(JWTBearer())):
    """
    Get a dailyhack from an event
    """
    return await eventmanagment_service.get_dailyhack(
        event_id, hacker_id, db, get_data_from_token(token))


@router.delete("/{event_id}/dailyhack/{hacker_id}")
async def delete_dailyhack(event_id: int,
                           hacker_id: int,
                           db: Session = Depends(get_db),
                           token: str = Depends(JWTBearer())):
    """
     Delete a dailyhack from an event
     """
    return await eventmanagment_service.delete_dailyhack(
        event_id, hacker_id, db, get_data_from_token(token))


@router.get("/{event_id}/dailyhacks")
async def get_dailyhacks(event_id: int,
                         db: Session = Depends(get_db),
                         token: str = Depends(JWTBearer())):
    """
    Get all dailyhacks from an event
    """
    return await eventmanagment_service.get_dailyhacks(
        event_id, db, get_data_from_token(token))


@router.put("/{event_id}/register/{hacker_id}")
async def register_hacker_to_event(event_id: int,
                                   hacker_id: str,
                                   registration: SchemaEventRegistration,
                                   db: Session = Depends(get_db),
                                   token: str = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    hacker = await hacker_service.get_hacker(hacker_id, db,
                                             get_data_from_token(token))
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
    hacker = await hacker_service.get_hacker(hacker_id, db,
                                             get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.unregister_hacker_from_event(
        event, hacker, db, get_data_from_token(token))


@router.get("/confirm-assistance")
async def confirm_assistance(token: str, db: Session = Depends(get_db)):
    """
    Confirm assistance of a hacker to an event
    """
    await eventmanagment_service.confirm_assistance(token, db)
    #redirect to Configuration.get('OTHERS', 'FRONT_URL')
    return Response(
        status_code=303,
        headers={"Location": Configuration.get('OTHERS', 'FRONT_URL')})


@router.put("/{event_id}/participate/{hacker_code}")
async def participate_hacker_to_event(event_id: int,
                                      hacker_code: str,
                                      db: Session = Depends(get_db),
                                      token: str = Depends(JWTBearer())):
    """
    Participate a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker_by_code(hacker_code, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    m,reg = await eventmanagment_service.participate_hacker_to_event(
        event, hacker, db, get_data_from_token(token))
    return {
        'success': True,
        'event_id': event.id,
        'hacker_id': hacker.id,
        'hacker_name': hacker.name,
        'hacker_shirt_size': reg.shirt_size,
        'food_restrictions': reg.food_restrictions,
        'message':m, 
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
    hacker = await hacker_service.get_hacker(hacker_id, db,
                                             get_data_from_token(token))
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
    hacker = await hacker_service.get_hacker(hacker_id, db,
                                             get_data_from_token(token))
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.accept_hacker_to_event(
        event, hacker, db, get_data_from_token(token))


@router.put("/{event_id}/unaccept/{hacker_email}")
async def unaccept_hacker_from_event_by_email(event_id: int,
                                              hacker_email: str,
                                              db: Session = Depends(get_db),
                                              token: str = Depends(
                                                  JWTBearer())):
    """
    Unaccept a hacker from an event by email
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker_by_email(hacker_email, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return await eventmanagment_service.unaccept_hacker_to_event(
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
    hacker = await hacker_service.get_hacker(hacker_id, db,
                                             get_data_from_token(token))
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
        'hackers': subtract_lists(event.registered_hackers,
                                  event.accepted_hackers)
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
async def get_event_status(event_id: int, db: Session = Depends(get_db)):
    """
    Get the status of an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_event_status(event, db)


@router.get("/{event_id}/food_restrictions")
async def get_food_restrictions(event_id: int, db: Session = Depends(get_db)):
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_food_restrictions(event, db)


@router.put("/{event_id}/eat/{meal_id}/{hacker_code}")
async def eat(event_id: int,
              meal_id: int,
              hacker_code: str,
              db: Session = Depends(get_db),
              token: str = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    hacker = await hacker_service.get_hacker_by_code(hacker_code, db)
    if hacker is None:
        raise NotFoundException("Hacker not found")
    meal = [meal for meal in event.meals if meal.id == meal_id][0]
    return await eventmanagment_service.eat(event, meal, hacker, db,
                                            get_data_from_token(token))


# def test(lst, background_tasks: BackgroundTasks):
#     for u in lst:
#         mail_service.send_reminder_email(u)
#         time.sleep(10)


# background_tasks.add_task(mail_service.send_reminder_email, u)
@router.post("/{event_id}/send_remember")
async def send_remember(
    event_id: int,
    # background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(JWTBearer())):
    """
    Send a remember notification to all attendees of an event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    all = await hacker_service.get_all(db)
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    users = subtract_lists(all, event.registered_hackers)
    return await mail_service.send_all_reminder_mails(users)


@router.post("/{event_id}/send_dailyhack")
async def send_dailyhack(event_id: int,
                         background_tasks: BackgroundTasks,
                         db: Session = Depends(get_db),
                         token: str = Depends(JWTBearer())):
    """
    Send a daily hack notification to all attendees of an event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await mail_service.send_all_dailyhack_mails(event.registered_hackers
                                                       )


@router.get("/{event_id}/get_sizes")
async def get_sizes(event_id: int, db: Session = Depends(get_db)):
    """
    Get the sizes of all the shirts of the registered hackers
    """
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_sizes(event, db)


@router.get("/{event_id}/get_unregistered_hackers")
async def get_unregistered_hackers(event_id: int,
                                   db: Session = Depends(get_db),
                                   token: str = Depends(JWTBearer())):
    """
    Get the hackers who are not registered for the event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.get_hackers_unregistered(event, db)


@router.get("/{event_id}/count_unregistered_hackers")
async def count_unregistered_hackers(event_id: int,
                                     db: Session = Depends(get_db),
                                     token: str = Depends(JWTBearer())):
    """
    Get the count of hackers who are not registered for the event
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    event = await event_service.get_event(event_id, db)
    if event is None:
        raise NotFoundException("Event not found")
    return await eventmanagment_service.count_hackers_unregistered(event, db)
