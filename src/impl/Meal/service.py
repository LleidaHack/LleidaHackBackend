from pydantic import parse_obj_as
from error.InvalidDataException import InvalidDataException
from src.impl.Meal.model import Meal as ModelMeal
from src.utils.UserType import UserType

from src.impl.Meal.schema import MealCreate as MealCreateSchema
from src.impl.Meal.schema import MealUpdate as MealUpdateSchema
from src.impl.Meal.schema import MealGet as MealGetSchema
from src.impl.Meal.schema import MealGetAll as MealGetAllSchema

from src.utils.Base.BaseService import BaseService

from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken

from src.error.AuthenticationException import AuthenticationException
from src.error.NotFoundException import NotFoundException

import src.impl.Event.service as E_S
import src.impl.Hacker.service as H_S


class MealService(BaseService):

    def __call__(self):
        if self.hacker_service is None:
            self.hacker_service = H_S.HackerService()
        if self.event_service is None:
            self.event_service = E_S.EventService()

    def get_all(self, id: int):
        return self.db.query(ModelMeal).filter(ModelMeal.event_id == id).all()

    def get_by_id(self, id: int):
        meal = self.db.query(ModelMeal).filter(ModelMeal.id == id).first()
        if meal is None:
            raise NotFoundException("Meal not found")
        return meal

    def get_meal(self, id: int, data: BaseToken):
        meal = self.get_by_id(id)
        if data.check([UserType.LLEIDAHACKER]):
            return parse_obj_as(MealGetAllSchema, meal)
        return parse_obj_as(MealGetSchema, meal)

    def add_meal(self, meal: MealCreateSchema, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to add meals")
        db_meal = ModelMeal(**meal.dict())
        self.db.add(db_meal)
        self.db.commit()
        self.db.refresh(db_meal)
        return db_meal

    def update_meal(self, id: int, meal_id: int, meal: MealUpdateSchema,
                    data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to update meals")
        db_meal = self.get_by_id(meal_id)
        set_existing_data(db_meal, meal)
        self.db.commit()
        self.db.refresh(db_meal)
        return db_meal

    def delete_meal(self, id: int, meal_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to delete meals")
        db_meal = self.get_by_id(meal_id)
        self.db.delete(db_meal)
        self.db.commit()
        return db_meal

    def eat(self, meal_id: int, hacker_code: str, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("Not authorized")
        hacker = self.hacker_service.get_by_code(hacker_code)
        meal = self.get_by_id(meal_id)
        event = self.event_service.get_by_id(meal.event_id)
        if not hacker in event.participants:
            raise InvalidDataException("Hacker not participating")
        if hacker in meal.users:
            raise InvalidDataException("Hacker already eating")
        meal.users.append(hacker)
        self.db.commit()
        self.db.refresh(event)
        return event
