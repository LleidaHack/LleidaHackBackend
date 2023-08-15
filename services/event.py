from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Company import Company as ModelCompany
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup
from models.TokenData import TokenData

from security import check_image_exists

async def get_all(db: Session):
    return db.query(ModelEvent).all()


async def get_event(id: int, db: Session):
    return db.query(ModelEvent).filter(ModelEvent.id == id).first()


async def add_event(event: SchemaEvent, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
            raise Exception("Not authorized")
    db_event = ModelEvent(name=event.name,
                          description=event.description,
                          start_date=event.start_date,
                          end_date=event.end_date,
                          location=event.location,
                          archived=event.archived,
                          status=event.status,
                          price=event.price,
                          max_participants=event.max_participants,
                          max_sponsors=event.max_sponsors)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


async def update_event(id: int, event: SchemaEvent, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
            raise Exception("Not authorized")
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if db_event is None:
        raise Exception("Event not found")
    db_event.name = event.name
    db_event.description = event.description
    db_event.start_date = event.start_date
    db_event.end_date = event.end_date
    db_event.location = event.location
    db.commit()
    return db_event


async def delete_event(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
            raise Exception("Not authorized")
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if db_event is None:
        raise Exception("Event not found")
    db.delete(db_event)
    db.commit()
    return db_event

async def get_event_participants(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "company"):
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    return event.hackers

async def get_event_sponsors(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    return event.sponsors

async def get_event_groups(id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "company"):
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    return event.hacker_groups

async def set_event_logo(id: int, logo_id: str, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
            raise Exception("Not authorized")
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if db_event is None:
        raise Exception("Event not found")
    if check_image_exists(logo_id):
        raise Exception("Logo not found")
    db_event.logo_id = logo_id
    db.commit()
    db.refresh(db_event)
    return db_event


async def add_company(id: int, company_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
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

async def add_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "hacker") or hacker_id != data.user_id:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    if hacker is None:
        raise Exception("Hacker not found")
    if not data.is_admin:
        if event.max_participants <= len(event.hackers):
            raise Exception("Event is full")
    event.hackers.append(hacker)
    db.commit()
    db.refresh(event)
    db.refresh(hacker)
    return event


async def add_hacker_group(id: int, hacker_group_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "hacker"):
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
        if event.max_participants <= len(event.hackers) + len(hacker_group.hackers):
            raise Exception("Event is full")
    event.hacker_groups.append(hacker_group)
    event.hackers.extend(hacker_group.hackers)
    db.commit()
    db.refresh(event)
    return event


async def remove_company(id: int, company_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or data.type != "lleida_hacker":
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


async def remove_hacker(id: int, hacker_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "hacker") or hacker_id != data.user_id:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    if hacker is None:
        raise Exception("Hacker not found")
    if hacker not in event.hackers:
        raise Exception("Hacker is not participant")
    event.hackers.remove(hacker)
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker.hacker_group_id).first()
    if hacker_group is not None:
        hacker_group.hackers.remove(hacker)
    db.commit()
    db.refresh(hacker_group)
    db.refresh(hacker)
    db.refresh(event)
    return event


async def remove_hacker_group(id: int, hacker_group_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.available or not (data.type == "lleida_hacker" or data.type == "hacker"):
            raise Exception("Not authorized")
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker_group_id).first()
    if hacker_group is None:
        raise Exception("Hacker group not found")
    group_hackers = [hacker.id for hacker in hacker_group.hackers]
    if not data.is_admin:
        if data.user_id not in group_hackers or hacker_group.leader_id != data.user_id:
            raise Exception("Not authorized")
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    if event is None:
        raise Exception("Event not found")
    event.hacker_groups.remove(hacker_group)
    for hacker in hacker_group.hackers:
        event.hackers.remove(hacker)
    db.commit()
    db.refresh(hacker_group)
    db.refresh(event)
    return event
