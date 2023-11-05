from multiprocessing import Event
from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import HackerEventRegistration as SchemaEventRegistration

from models.Event import Event as ModelEvent
from models.Event import HackerRegistration as ModelHackerRegistration
from models.Meal import Meal as ModelMeal
from models.Hacker import HackerGroupUser as ModelHackerGroupUser
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup
from models.TokenData import TokenData
from models.UserType import UserType

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.InvalidDataException import InvalidDataException
from security import create_all_tokens, get_data_from_token, generate_assistance_token

from utils.service_utils import isBase64, subtract_lists

from services.mail import send_dailyhack_added_email
from services.mail import send_event_registration_email
from services.mail import send_event_accepted_email


async def add_dailyhack(eventId: int, hackerId: int, url: str, db: Session,
                        data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hackerId,
        ModelHackerRegistration.event_id == eventId).first()
    if hacker_registration is None:
        raise NotFoundException("Hacker not registered")
    hacker_registration.dailyhack_url = url
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hackerId).first()
    await send_dailyhack_added_email(hacker)
    db.commit()
    db.refresh(hacker_registration)
    return hacker_registration


async def get_dailyhack(eventId: int, hackerId: int, db: Session,
                        data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hackerId,
        ModelHackerRegistration.event_id == eventId).first()
    if hacker_registration is None:
        raise NotFoundException("Hacker not registered")
    return hacker_registration.dailyhack_url


async def update_dailyhack(eventId: int, hackerId: int, url: str, db: Session,
                           data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hackerId,
        ModelHackerRegistration.event_id == eventId).first()
    if hacker_registration is None:
        raise NotFoundException("Hacker not registered")
    hacker_registration.dailyhack_url = url
    db.commit()
    db.refresh(hacker_registration)
    return hacker_registration


async def delete_dailyhack(eventId: int, hackerId: int, db: Session,
                           data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
                                    (data.type == UserType.HACKER.value
                                     and data.user_id == hackerId))):
            raise AuthenticationException("Not authorized")
    hacker_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == hackerId,
        ModelHackerRegistration.event_id == eventId).first()
    if hacker_registration is None:
        raise NotFoundException("Hacker not registered")
    hacker_registration.dailyhack_url = ""
    db.commit()
    db.refresh(hacker_registration)
    return hacker_registration


async def get_dailyhacks(eventId: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    registrations = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.event_id == eventId).all()
    event = db.query(ModelEvent).filter(ModelEvent.id == eventId).first()
    userid_dailyhack = []

    for registration in registrations:
        user = db.query(ModelHacker).filter(
            ModelHacker.id == registration.user_id).first()
        if user in event.accepted_hackers:
            userid_dailyhack.append({
                "id": registration.user_id,
                "name": user.name,
                "email": user.email,
                "dailyhack": registration.dailyhack_url
            })
    return userid_dailyhack


async def register_hacker_to_event(payload: SchemaEventRegistration,
                                   event: ModelEvent, hacker: ModelHacker,
                                   db: Session, data: TokenData):
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
    await send_event_registration_email(hacker, event)
    return event


async def unregister_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                       db: Session, data: TokenData):
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


async def confirm_assistance(token: str, db: Session):
    data = get_data_from_token(token, special=True)
    # if data.expt < datetime.utcnow().isoformat():
    user = db.query(ModelHacker).filter(ModelHacker.id == data.user_id).first()
    if user is None:
        raise InvalidDataException("User not found")
    event = db.query(ModelEvent).filter(ModelEvent.id == data.event_id).first()
    if event is None:
        raise InvalidDataException("Event not found")
    user_registration = db.query(ModelHackerRegistration).filter(
        ModelHackerRegistration.user_id == data.user_id,
        ModelHackerRegistration.event_id == data.event_id).first()
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


async def participate_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                      db: Session, data: TokenData):
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
    if not user_registration.confirmed_assistance:
        raise InvalidDataException("User not confirmed assitence")
    event.participants.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return user_registration


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


async def unaccept_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                   db: Session, data: TokenData):
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


async def accept_hacker_to_event(event: ModelEvent, hacker: ModelHacker,
                                 db: Session, data: TokenData):
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
    token = generate_assistance_token(hacker.id, event.id, db)
    hacker_registration.confirm_assistance_token = token
    event.accepted_hackers.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    await send_event_accepted_email(hacker, event, token)
    return event


async def accept_group_to_event(event: ModelEvent, group: ModelHackerGroup,
                                db: Session, data: TokenData):
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


async def reject_group_from_event(event: ModelEvent, group: ModelHackerGroup,
                                  db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    for hacker in group.members and hacker not in event.accepted_hackers:
        if hacker not in event.registered_hackers:
            raise InvalidDataException("Hacker not registered")
        event.rejected_hackers.append(hacker)


async def reject_hacker_from_event(event: ModelEvent, hacker: ModelHacker,
                                   db: Session, data: TokenData):
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


async def get_pending_hackers_gruped(event: ModelEvent, db: Session,
                                     data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    # Extract hacker IDs from registered_hackers
    pending_hackers = subtract_lists(event.registered_hackers,
                                     event.accepted_hackers)
    pending_hackers_ids = [
        h.id for h in subtract_lists(event.registered_hackers,
                                     event.accepted_hackers)
    ]
    # Retrieve pending hacker groups
    pending_groups_ids = db.query(ModelHackerGroupUser.group_id).filter(
        ModelHackerGroupUser.hacker_id.in_(pending_hackers_ids)).all()
    pending_groups_ids = [g[0] for g in pending_groups_ids]
    #remove duplicates
    pending_groups_ids = list(dict.fromkeys(pending_groups_ids))
    pending_groups = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id.in_(pending_groups_ids)).all()
    # return pending_groups_ids
    # Collect group users' IDs
    group_users = [
        hacker.id for group in pending_groups for hacker in group.members
    ]
    # Prepare the output data
    output_data = []
    for group in pending_groups:
        group_data = {
            "name":
            group.name,
            "members": [{
                "id": hacker.id,
                "name": hacker.name,
                "birthdate": hacker.birthdate,
                "address": hacker.address,
                "food_restrictions": hacker.food_restrictions,
                "shirt_size": hacker.shirt_size,
                "approved": hacker in event.accepted_hackers,
            } for hacker in group.members]
        }
        output_data.append(group_data)
    # Handle hackers without a group
    nogroup_data = [{
        "id": hacker.id,
        "name": hacker.name,
        "birthdate": hacker.birthdate,
        "address": hacker.address,
        "food_restrictions": hacker.food_restrictions,
        "shirt_size": hacker.shirt_size,
        "approved": hacker in event.accepted_hackers,
    } for hacker in subtract_lists(event.registered_hackers,
                                   event.accepted_hackers)
                    if hacker.id not in group_users]

    # Combine group and nogroup data into a dictionary
    return {"groups": output_data, "nogroup": nogroup_data}


# async def get_pending_hackers_gruped(event: ModelEvent, db: Session, data: TokenData):
#     if not data.is_admin:
#         if not (data.available and data.type == UserType.LLEIDAHACKER.value):
#             raise AuthenticationException("Not authorized")
#     pending_hackers_ids = [h.id for h in subtract_lists(event.registered_hackers, event.accepted_hackers)]
#     #get pending hacker groups
#     pending_groups = db.query(ModelHackerGroup).filter(ModelHackerGroup.id.in_(pending_hackers_ids)).all()
#     group_users = [hacker.id for group in pending_groups for hacker in group.members]
#     #join groups and hackers
#     out = "[{groups: ["
#     for group in pending_groups:
#         out += "{" + group.name + ": ["
#         for hacker in group.members:
#             out += "{" + str(hacker.id) + ", " + hacker.name + "," + str(hacker.birthdate) + "," + hacker.address + "," + hacker.food_restrictions + "," + hacker.shirt_size + "},"
#         out += "]},"
#     out += "{nogroup: ["
#     for hacker in subtract_lists(event.registered_hackers, group_users):
#         out += "{" + str(hacker.id) + ", " + hacker.name + "," + str(hacker.birthdate) + "," + hacker.address + "," + hacker.food_restrictions + "," + hacker.shirt_size + "},"
#     out += "]}]"
#     return out


async def get_event_status(event: ModelEvent, db: Session):
    data = {
        'registratedUsers':
        len(event.registered_hackers),
        'groups':
        len(event.groups),
        'acceptedUsers':
        len(event.accepted_hackers),
        'rejectedUsers':
        len(event.rejected_hackers),
        'participatingUsers':
        len(event.participants),
        'acceptedAndConfirmedUsers':
        len(await get_accepted_and_confirmed(event, db)),
    }
    for meal in event.meals:
        data[meal.name] = len(meal.users)
    return data


async def get_food_restrictions(event: ModelEvent, db: Session):
    users = event.participants + event.accepted_hackers + event.registered_hackers
    restrictions = []
    for user in users:
        if user.food_restrictions is not None and user.food_restrictions.strip(
        ) != "" and user.food_restrictions.strip() != 'no':
            restrictions.append(user.food_restrictions)
    # remove duplicates
    restrictions = list(set(restrictions))
    return restrictions


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


async def get_sizes(event: ModelEvent, db: Session):
    sizes = {}
    for user in event.registered_hackers:
        if user.shirt_size is not None and user.shirt_size.strip() != "":
            if user.shirt_size in sizes:
                sizes[user.shirt_size] += 1
            else:
                sizes[user.shirt_size] = 1
    return sizes


async def get_accepted_and_confirmed(event: ModelEvent, db: Session):
    accepted_and_confirmed = []
    for user in event.accepted_hackers:
        user_registration = db.query(ModelHackerRegistration).filter(
            ModelHackerRegistration.user_id == user.id,
            ModelHackerRegistration.event_id == event.id).first()
        if user_registration and user_registration.confirmed_assistance:
            accepted_and_confirmed.append(user)
    return accepted_and_confirmed

async def get_hackers_unregistered(event: ModelEvent, db: Session):
    hackers = db.query(ModelHacker).all()
    return subtract_lists(hackers, event.registered_hackers) 

async def count_hackers_unregistered(event: ModelEvent, db: Session):
    return len(get_hackers_unregistered(event, db))
