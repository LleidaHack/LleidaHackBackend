from models.Meal import Meal as ModelMeal
from models.TokenData import TokenData
from models.UserType import UserType

from schemas.Meal import Meal as SchemaMeal
from schemas.Meal import MealUpdate as SchemaMealUpdate

from sqlalchemy.orm import Session

from utils.service_utils import set_existing_data, check_image

from error.AuthenticationException import AuthenticationException
from error.NotFoundException import NotFoundException
from error.ValidationException import ValidationException


async def get_meals(id: int, db: Session, token: TokenData):
    return db.query(ModelMeal).filter(ModelMeal.event_id == id).all()


async def get_meal(id: int, meal_id: int, db: Session, token: TokenData):
    meal = db.query(ModelMeal).filter(ModelMeal.id == meal_id).first()
    if meal is None:
        raise NotFoundException("Meal not found")
    return meal


async def add_meal(meal: SchemaMeal, db: Session, data: TokenData):
    if not data.is_admin:
        if not data.type == UserType.LLEIDAHACKER.value:
            raise AuthenticationException("You are not allowed to add meals")
    db_meal = ModelMeal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal


async def update_meal(id: int, meal_id: int, meal: SchemaMealUpdate,
                      db: Session, data: TokenData):
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


async def delete_meal(id: int, meal_id: int, db: Session, data: TokenData):
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
