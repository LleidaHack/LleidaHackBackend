from sqlalchemy.orm import Session

from src.impl.Geocaching.model import Geocaching as ModelGeocaching
from src.impl.Geocaching.model import UserGeocaching as ModelUserGeocaching
from src.impl.User.model import User as ModelUser


def get_all_geocachings(db: Session):
    return db.query(ModelGeocaching).all()


def get_geocaching(db: Session, code: str):
    return db.query(ModelGeocaching).filter(
        ModelGeocaching.code == code).first()


def get_all_hacker_geocaching(db: Session, user_code: str):
    return db.query(ModelUserGeocaching).filter(
        ModelUserGeocaching.user_code == user_code).all()


def add_user_geocaching(db: Session, user_code: str, code: str):
    user_geocaching = ModelUserGeocaching(user_code=user_code, code=code)
    db.add(user_geocaching)
    db.commit()
    db.refresh(user_geocaching)
    return 'point cached'


def claim_lleidacoins(db: Session, user_code: str):
    hacker = db.query(ModelUser).filter(ModelUser.code == user_code).first()
    if hacker is None:
        raise ValueError("Hacker not found")
    all_geocachings = get_all_geocachings(db)
    hacker_geocachings = get_all_hacker_geocaching(db, user_code)
    if not len(all_geocachings) == len(hacker_geocachings):
        return 'User dont have all geocachings'
    hacker.lleidacoins_claimed = True
    db.commit()
    db.refresh(hacker)
    return 'claimed succesfully'
