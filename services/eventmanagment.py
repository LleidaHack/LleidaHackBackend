from multiprocessing import Event
from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Meal import Meal as ModelMeal
from models.Hacker import Hacker as ModelHacker
from models.TokenData import TokenData
from models.UserType import UserType

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException


async def register_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                   db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hacker.id))):
            raise AuthenticationException("Not authorized")
    if hacker in event.registered_hackers or hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already registered")
    if len(event.registered_hackers) >= event.max_participants:
        raise InvalidDataException("Event full")
    event.registered_hackers.append(hacker)
    db.commit()
    db.refresh(event)
    return event


async def unregister_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                       db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hacker.id))):
            raise AuthenticationException("Not authorized")
    if not (hacker in event.registered_hackers
            or hacker in event.accepted_hackers):
        raise InvalidDataException("Hacker not registered")
    if hacker in event.participants:
        raise InvalidDataException("Hacker already participating")
    if hacker in event.accepted_hackers:
        event.accepted_hackers.remove(hacker)
    else:
        event.registered_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    return event


async def participate_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                      db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if hacker in event.participants:
        raise InvalidDataException("Hacker already participating")
    if not hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker not accepted")
    event.participants.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


async def unparticipate_hacker_from_event(event: ModelEvent,
                                          hacker: ModelHacker, db: Session,
                                          data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.participants:
        raise InvalidDataException("Hacker not participating")
    event.participants.remove(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


async def accept_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                 db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    if hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already accepted")
    event.accepted_hackers.append(hacker)
    event.registered_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


async def reject_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                   db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    if hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already accepted")
    event.registered_hackers.append(hacker)
    event.accepted_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


async def get_event_status(event: ModelEvent, db: Session):
    data = {
        'registratedUsers':
        len(event.registered_hackers) + len(event.accepted_hackers),
        'acceptedUsers':
        len(event.accepted_hackers),
        'participatingUsers':
        len(event.participants),
    }
    for meal in event.meals:
        data[meal.name] = len(meal.users)


async def eat(event: ModelEvent, meal: ModelMeal, hacker: ModelHacker,
              db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.participants:
        raise InvalidDataException("Hacker not participating")
    if hacker in meal.users:
        raise InvalidDataException("Hacker already eating")
    meal.users.append(hacker)
    db.commit()
    db.refresh(event)
    return event
