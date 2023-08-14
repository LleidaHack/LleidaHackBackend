from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Company import Company as ModelCompany
from models.Hacker import Hacker as ModelHacker
from models.Hacker import HackerGroup as ModelHackerGroup


async def get_all(db: Session):
    return db.query(ModelEvent).all()


async def get_event(id: int, db: Session):
    return db.query(ModelEvent).filter(ModelEvent.id == id).first()


async def add_event(event: SchemaEvent, db: Session):
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


async def update_event(id: int, event: SchemaEvent, db: Session):
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    db_event.name = event.name
    db_event.description = event.description
    db_event.start_date = event.start_date
    db_event.end_date = event.end_date
    db_event.location = event.location
    db.commit()
    return db_event


async def delete_event(id: int, db: Session):
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    db.delete(db_event)
    db.commit()
    return db_event


async def set_event_logo(id: int, logo_id: str, db: Session):
    db_event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    db_event.logo_id = logo_id
    db.commit()
    return db_event


async def add_company(id: int, company_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    company = db.query(ModelCompany).filter(
        ModelCompany.id == company_id).first()
    event.companies.append(company)
    db.commit()
    db.refresh(event)
    return event


async def add_hacker(id: int, hacker_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    event.hackers.append(hacker)
    db.commit()
    db.refresh(event)
    return event


async def add_hacker_group(id: int, hacker_group_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker_group_id).first()
    event.hacker_groups.append(hacker_group)
    db.commit()
    db.refresh(event)
    return event


async def remove_company(id: int, company_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    company = db.query(ModelCompany).filter(
        ModelCompany.id == company_id).first()
    event.companies.remove(company)
    db.commit()
    db.refresh(event)
    return event


async def remove_hacker(id: int, hacker_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    hacker = db.query(ModelHacker).filter(ModelHacker.id == hacker_id).first()
    event.hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    return event


async def remove_hacker_group(id: int, hacker_group_id: int, db: Session):
    event = db.query(ModelEvent).filter(ModelEvent.id == id).first()
    hacker_group = db.query(ModelHackerGroup).filter(
        ModelHackerGroup.id == hacker_group_id).first()
    event.hacker_groups.remove(hacker_group)
    db.commit()
    db.refresh(event)
    return event
