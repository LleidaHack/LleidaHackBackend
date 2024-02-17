from pydantic import parse_obj_as
from src.Meal.model import Meal as ModelMeal
from src.Utils.TokenData import TokenData
from src.Utils.UserType import UserType

from src.Meal.schema import MealCreate as MealCreateSchema
from src.Meal.schema import MealUpdate as MealUpdateSchema
from src.Meal.schema import MealGet as MealGetSchema
from src.Meal.schema import MealGetAll as MealGetAllSchema

from sqlalchemy.orm import Session

from utils.service_utils import set_existing_data

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException


def get_meals(id: int, db: Session, token: TokenData):
    return db.query(ModelMeal).filter(ModelMeal.event_id == id).all()


def get_meal(id: int, db: Session, data: TokenData):
    meal = db.query(ModelMeal).filter(ModelMeal.id == id).first()
    if meal is None:
        raise NotFoundException("Meal not found")
    if data.is_admin or (data.available and data.type == UserType.LLEIDAHACKER.value):
        return parse_obj_as(MealGetAllSchema, meal)
    return parse_obj_as(MealGetSchema, meal)


def add_meal(meal: MealCreateSchema, db: Session, data: TokenData):
    if not data.is_admin:
        if not (data.available and data.type == UserType.LLEIDAHACKER.value):
            raise AuthenticationException("You are not allowed to add meals")
    db_meal = ModelMeal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal


def update_meal(id: int, meal_id: int, meal: MealUpdateSchema, db: Session,
                data: TokenData):
    if not data.is_admin:
        if not data.type == UserType.LLEIDAHACKER.value:
            raise AuthenticationException(
                "You are not allowed to update meals")
    db_meal = db.query(ModelMeal).filter(ModelMeal.id == meal_id).first()
    if db_meal is None:
        raise NotFoundException("Meal not found")
    set_existing_data(db_meal, meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal


def delete_meal(id: int, meal_id: int, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.type == UserType.LLEIDAHACKER.value:
            raise AuthenticationException(
                "You are not allowed to delete meals")
    db_meal = db.query(ModelMeal).filter(ModelMeal.id == meal_id).first()
    if db_meal is None:
        raise NotFoundException("Meal not found")
    db.delete(db_meal)
    db.commit()
    return db_meal
