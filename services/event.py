from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent
from schemas.Event import EventUpdate as SchemaEventUpdate

from models.Event import Event as ModelEvent
from models.Company import Company as ModelCompany
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup
from models.Hacker import HackerGroupUser as ModelHackerGroupUser
from models.Hacker import HackerGroup as ModelHackerGroup

from models.TokenData import TokenData
from models.UserType import UserType

from utils.service_utils import set_existing_data, check_image
from utils.hide_utils import hacker_show_private

from error.AuthenticationException import AuthenticationException
from error.ValidationException import ValidationException
from error.NotFoundException import NotFoundException


async def get_all(db: Session):
    return db.query(ModelEvent).all()


async def get_hackeps(year: int, db: Session):
    #return and event called HackEPS year ignoring caps
    e = db.query(ModelEvent).filter(
        ModelEvent.name.ilike(f'%HackEPS {str(year)}%')).first()
    if e is None:
        return db.query(ModelEvent).filter(
            ModelEvent.name.ilike(f'%HackEPS {str(year-1)}%')).first()
    return e


async def get_hacker_group(event_id: int, hacker_id: int, db: Session,
                           data: TokenData):
    event = db.query(ModelEvent).filter(ModelEvent.id == event_id).first()
    if event is None:
        raise NotFoundException("Event not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    if hacker not in event.registered_hackers:
        raise NotFoundException("Hacker is not participant")
    user_groups = db.query(ModelHackerGroupUser).filter(
        ModelHackerGroupUser.hacker_id == hacker_id).all()
    group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.event_id == event_id).filter(
            ModelHackerGroup.id.in_([g.hacker_group_id
                                     for g in user_groups])).first()
    return group


async def get_event(id: int, db: Session):
    return db.query(ModelEvent).filter(ModelEvent.id == id).first()


async def add_event(payload: SchemaEvent, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    if payload.image is not None:
        payload = check_image(payload)
    db_event = ModelEvent(**payload.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


async def update_event(id: int, event: SchemaEventUpdate, db: Session,
                       data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if db_event is None:
        raise NotFoundException("Event not found")
    if event.image is not None:
        event = check_image(event)
    updated = set_existing_data(db_event, event)
    db.commit()
    return db_event, updated


async def delete_event(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("Not authorized")
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if db_event is None:
        raise NotFoundException("Event not found")
    db.delete(db_event)
    db.commit()
    return db_event


async def is_registered(id: int, hacker_id: int, db: Session, data: TokenData):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise NotFoundException("Event not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return hacker in event.registered_hackers


async def is_accepted(id: int, hacker_id: int, db: Session, data: TokenData):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise NotFoundException("Event not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    if hacker is None:
        raise NotFoundException("Hacker not found")
    return hacker in event.accepted_hackers


async def get_event_meals(id: int, db: Session, data: TokenData):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise NotFoundException("Event not found")
    return event.meals


async def get_event_participants(id: int, db: Session, data: TokenData):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise NotFoundException("Event not found")
    return event.registered_hackers


async def get_event_sponsors(id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise NotFoundException("Event not found")
    return event.sponsors


async def get_event_groups(id: int, db: Session, data: TokenData):
    event = db.query(ModelHackerGroup).filter(ModelHackerGroup.event_id == id)
    if event is None:
        raise NotFoundException("Event not found")
    return event


async def add_company(id: int, company_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == company_id).first()
    if company is None:
        raise Exception("Company not found")
    event.sponsors.append(company)
    db.commit()
    db.refresh(event)
    db.refresh(company)
    return event


# async def add_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
#     if not data.is_admin:
#         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
#                                     (data.type == UserType.HACKER.value
#                                      and hacker_id != data.user_id))):
#             raise Exception("Not authorized")
#     event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
#     if event is None:
#         raise Exception("Event not found")
#     hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
#     if hacker is None:
#         raise Exception("Hacker not found")
#     if not data.is_admin:
#         if event.max_participants <= len(event.hackers):
#             raise Exception("Event is full")
#     event.hackers.append(hacker)
#     db.commit()
#     db.refresh(event)
#     db.refresh(hacker)
#     return event


async def add_hacker_group(id: int, hacker_group_id: int, db: Session,
                           data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise Exception("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker_group_id).first()
    grou_hackers = [hacker.id for hacker in hacker_group.hackers]
    if not data.is_admin:
        if data.user_id not in grou_hackers or hacker_group.leader_id != data.user_id:
            raise Exception("Not authorized")
    if hacker_group is None:
        raise Exception("Hacker group not found")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    if not data.is_admin:
        if event.max_participants <= len(event.hackers) + len(
                hacker_group.hackers):
            raise Exception("Event is full")
    event.hacker_groups.append(hacker_group)
    event.hackers.extend(hacker_group.hackers)
    db.commit()
    db.refresh(event)
    return event


async def remove_company(id: int, company_id: int, db: Session,
                         data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise Exception("Not authorized")
    company = db.query(ModelCompany).filter(
        ModelCompany.id == company_id).first()
    if company is None:
        raise Exception("Company not found")
    company_users = [user.id for user in company.users]
    if not data.is_admin:
        if data.user_id not in company_users:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    if company not in event.companies:
        raise Exception("Company is not sponsor")
    event.companies.remove(company)
    db.commit()
    db.refresh(event)
    db.refresh(company)
    return event

    # async def remove_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
    #     if not data.is_admin:
    #         if not (data.available and (data.type == UserType.LLEIDAHACKER.value or
    #                                     (data.type == UserType.HACKER.value
    #                                      and hacker_id != data.user_id))):
    #             raise Exception("Not authorized")
    #     event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    #     if event is None:
    #         raise Exception("Event not found")
    #     hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    #     if hacker is None:
    #         raise Exception("Hacker not found")
    #     if hacker not in event.hackers:
    #         raise Exception("Hacker is not participant")
    #     event.hackers.remove(hacker)
    #     hacker_group = db.query(ModelHackerGroup).filter(
    #         ModelHackerGroup.id == hacker.hacker_group_id).first()
    #     if hacker_group is not None:
    #         hacker_group.hackers.remove(hacker)
    #     db.commit()
    #     db.refresh(hacker_group)
    #     db.refresh(hacker)
    #     db.refresh(event)
    return event


async def remove_hacker_group(id: int, hacker_group_id: int, db: Session,
                              data: TokenData):
    if not data.is_admin:
        if not (data.available and (data.type == UserType.LLEIDAHACKER.value
                                    or data.type == UserType.HACKER.value)):
            raise Exception("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker_group_id).first()
    if hacker_group is None:
        raise Exception("Hacker group not found")
    group_hackers = [hacker.id for hacker in hacker_group.members]
    if not data.is_admin:
        if data.user_id not in group_hackers or hacker_group.leader_id != data.user_id:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    event.hacker_groups.remove(hacker_group)
    for hacker in hacker_group.members:
        event.registered_hackers.remove(hacker)
    db.commit()
    db.refresh(hacker_group)
    db.refresh(event)
    return event


async def get_accepted_hackers(event_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == event_id).first()
    if event is None:
        raise Exception("Event not found")
    hackers = []
    for h in event.accepted_hackers:
        hacker_show_private(h)
        hackers.append(h)
    return hackers


async def get_accepted_hackers_mails(event_id: int, db: Session,
                                     data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == event_id).first()
    if event is None:
        raise Exception("Event not found")
    hackers = []
    for h in event.accepted_hackers:
        hacker_show_private(h)
        hackers.append(h.email)
    return hackers
