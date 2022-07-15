from multiprocessing import Event
from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from schemas.Event import Event as SchemaEvent

from models.Event import Event as ModelEvent
from models.Meal import Meal as ModelMeal
from models.Hacker import Hacker as ModelHacker

def register_hacker_to_event(event:ModelEvent, hacker:ModelHacker, db:Session):
    event.registered_hackers.append(hacker)
    db.commit()
    db.refresh(event)
    return event

def unregister_hacker_from_event(event:ModelEvent, hacker:ModelHacker, db:Session):
    event.registered_hackers.remove(hacker)
    db.commit()
    db.refresh(event)
    return event

def get_event_status(event:ModelEvent, db:Session):
    return {
        'users': len(event.hackers), 
        'regUsers': len(event.registered_hackers), 
        'friDinner': len(event.meals[0].users), 
        'satLunch': len(event.meal[1].users), 
        'satDin': len(event.meal[2].users), 
        'sunLunch': len(event.meal[3].users)
    }

def eat(event:ModelEvent, meal:ModelMeal, hacker:ModelHacker, db:Session):
    meal.users.append(hacker)
    db.commit()
    db.refresh(event)
    return event