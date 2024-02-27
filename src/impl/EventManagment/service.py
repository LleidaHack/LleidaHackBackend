from multiprocessing import Event
from sqlalchemy.orm import Session

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException

from src.utils.UserType import UserType
from src.utils.Token import AssistenceToken
from src.utils.service_utils import isBase64, subtract_lists
from src.utils.Token import BaseToken

from src.impl.Event.model import Event as ModelEvent
from src.impl.Event.model import HackerRegistration as ModelHackerRegistration
from src.impl.Meal.model import Meal as ModelMeal
from src.impl.Hacker.model import Hacker as ModelHacker
from src.impl.HackerGroup.model import HackerGroup as ModelHackerGroup

from src.impl.Event.schema import HackerEventRegistration as EventRegistrationSchema

from services.mail import send_event_registration_email
from services.mail import send_event_accepted_email

# A PARTIR D'ARA EL SENYOR LOLO A.K.A LUFI ES DIRA LO-FI


def register_hacker_to_event(payload: EventRegistrationSchema,
                             event: ModelEvent, hacker: ModelHacker,
                             db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hacker.id))):
            raise AuthenticationException("Not authorized")
    if not event.is_open:
        raise InvalidDataException("Event registration not open")
    if hacker in event.registered_hackers or hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already registered")
    if len(event.registered_hackers) >= event.max_participants:
        raise InvalidDataException("Event full")
    if payload.cv != "" and not isBase64(payload.cv):
        raise InvalidDataException("Invalid CV")
    event_registration = ModelHackerRegistration(**payload.dict(),
                                                 user_id=hacker.id,
                                                 event_id=event.id,
                                                 confirmed_assistance=False,
                                                 confirm_assistance_token="")
    if payload.update_user:
        if hacker.cv != payload.cv:
            hacker.cv = payload.cv
        # if hacker.description != payload.description:
        #     hacker.description = payload.description
        if hacker.food_restrictions != payload.food_restrictions:
            hacker.food_restrictions = payload.food_restrictions
        if hacker.shirt_size != payload.shirt_size:
            hacker.shirt_size = payload.shirt_size
        if hacker.github != payload.github:
            hacker.github = payload.github
        if hacker.linkedin != payload.linkedin:
            hacker.linkedin = payload.linkedin
        if hacker.studies != payload.studies:
            hacker.studies = payload.studies
        if hacker.study_center != payload.study_center:
            hacker.study_center = payload.study_center
        if hacker.location != payload.location:
            hacker.location = payload.location
        if hacker.how_did_you_meet_us != payload.how_did_you_meet_us:
            hacker.how_did_you_meet_us = payload.how_did_you_meet_us
    db.add(event_registration)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    send_event_registration_email(hacker, event)
    return event


def unregister_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                 db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hacker.id))):
            raise AuthenticationException("Not authorized")
    if not event.is_open:
        raise InvalidDataException("Event registration not open")
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


def confirm_assistance(token: AssistenceToken, db: Session):
    # data = get_data_from_token(token, special=True)
    # if data.expt < datetime.utcnow().isoformat():
    user = db.query(ModelHacker).filter(
        ModelHacker.id == token.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    event = db.query(ModelEvent).filter(
        ModelEvent.id == token.event_id).first()
    if event is None:
        raise InvalidDataException("Event not found")
    user_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == token.user_id,
        ModelHackerRegistration.event_id == token.event_id).first()
    if user_registration is None:
        raise InvalidDataException("User not registered")
    if user_registration.confirm_assistance_token != token:
        raise InvalidDataException("Invalid token")
    if user not in event.accepted_hackers:
        raise InvalidDataException("User not accepted")
    if user_registration.confirmed_assistance:
        raise InvalidDataException("User already confirmed assistance")
    user_registration.confirmed_assistance = True
    db.commit()
    db.refresh(user_registration)
    return user_registration


def participate_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                db: Session, data: BaseToken):
    message = ''
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if hacker in event.participants:
        raise InvalidDataException("Hacker already participating")
    if not hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker not accepted")
    user_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hacker.user_id,
        ModelHackerRegistration.event_id == event.id).first()
    if user_registration is None:
        raise InvalidDataException("User not registered")
    # user_registration.confirmed_assistance = True
    if not user_registration.confirmed_assistance:
        message = "user haven't confirmed so we frced confirmation"
        # raise InvalidDataException("User not confirmed assitence")
    event.participants.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return message, user_registration


def unparticipate_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                    db: Session, data: BaseToken):
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


def unaccept_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                             db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker not accepted")
    event.accepted_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


def accept_hacker_to_event(event: ModelEvent, hacker: ModelHacker, db: Session,
                           data: BaseToken):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    if hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already accepted")
    hacker_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hacker.id,
        ModelHackerRegistration.event_id == event.id).first()
    if hacker_registration is None:
        raise InvalidDataException("Hacker not registered")
    token = AssistenceToken(hacker, event.id).to_token()
    hacker_registration.confirm_assistance_token = token
    event.accepted_hackers.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    send_event_accepted_email(hacker, event, token)
    return event


def accept_group_to_event(event: ModelEvent, group: ModelHackerGroup,
                          db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    for hacker in subtract_lists(group.members, event.accepted_hackers):
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        hacker_user = db.query(ModelHacker).filter(
            ModelHacker.id == hacker.id).first()
        if hacker_user is None:
            raise InvalidDataException("Hacker not registered")
        accept_hacker_to_event(event, hacker_user, db, data)


def reject_group_from_event(event: ModelEvent, group: ModelHackerGroup,
                            db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    for hacker in group.members and hacker not in event.accepted_hackers:
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        event.rejected_hackers.append(hacker)


def reject_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                             db: Session, data: BaseToken):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if not hacker in event.registered_hackers:
        raise InvalidDataException("Hacker not registered")
    if hacker in event.accepted_hackers:
        raise InvalidDataException("Hacker already accepted")
    event.rejected_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


def eat(event: ModelEvent, meal: ModelMeal, hacker: ModelHacker, db: Session,
        data: BaseToken):
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
