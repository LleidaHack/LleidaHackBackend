from pydantic import parse_obj_as
from src.impl.Meal.model import Meal as ModelMeal
from src.utils.TokenData import TokenData
from src.utils.UserType import UserType

from src.impl.Meal.schema import MealCreate as MealCreateSchema
from src.impl.Meal.schema import MealUpdate as MealUpdateSchema
from src.impl.Meal.schema import MealGet as MealGetSchema
from src.impl.Meal.schema import MealGetAll as MealGetAllSchema

from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException


class MealService(BaseService):

    def get_meals(self, id: int, token: TokenData):
        return self.db.query(ModelMeal).filter(ModelMeal.event_id == id).all()

    def get_meal(self, id: int, data: TokenData):
        meal = self.db.query(ModelMeal).filter(ModelMeal.id == id).first()
        if meal is None:
            raise NotFoundException("Meal not found")
        if data.is_admin or (data.available
                             and data.type == UserType.LLEIDAHACKER.value):
            return parse_obj_as(MealGetAllSchema, meal)
        return parse_obj_as(MealGetSchema, meal)

    def add_meal(self, meal: MealCreateSchema, data: TokenData):
        if not data.is_admin:
            if not (data.available
                    and data.type == UserType.LLEIDAHACKER.value):
                raise AuthenticationException(
                    "You are not allowed to add meals")
        db_meal = ModelMeal(**meal.dict())
        self.db.add(db_meal)
        self.db.commit()
        self.db.refresh(db_meal)
        return db_meal

    def update_meal(self, id: int, meal_id: int, meal: MealUpdateSchema,
                    data: TokenData):
        if not data.is_admin:
            if not data.type == UserType.LLEIDAHACKER.value:
                raise AuthenticationException(
                    "You are not allowed to update meals")
        db_meal = self.db.query(ModelMeal).filter(
            ModelMeal.id == meal_id).first()
        if db_meal is None:
            raise NotFoundException("Meal not found")
        set_existing_data(db_meal, meal)
        self.db.commit()
        self.db.refresh(db_meal)
        return db_meal

    def delete_meal(self, id: int, meal_id: int, data: TokenData):
        if not data.is_admin:
            if not data.type == UserType.LLEIDAHACKER.value:
                raise AuthenticationException(
                    "You are not allowed to delete meals")
        db_meal = self.db.query(ModelMeal).filter(
            ModelMeal.id == meal_id).first()
        if db_meal is None:
            raise NotFoundException("Meal not found")
        self.db.delete(db_meal)
        self.db.commit()
        return db_meal
