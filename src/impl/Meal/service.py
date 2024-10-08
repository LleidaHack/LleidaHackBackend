from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.Meal.model import Meal
from src.impl.Meal.schema import MealCreate
from src.impl.Meal.schema import MealGet
from src.impl.Meal.schema import MealGetAll
from src.impl.Meal.schema import MealUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class MealService(BaseService):
    name = 'meal_service'
    hacker_service = None
    event_service = None

    def get_all(self, id: int):
        return db.session.query(Meal).filter(Meal.event_id == id).all()

    def get_by_id(self, id: int):
        meal = db.session.query(Meal).filter(Meal.id == id).first()
        if meal is None:
            raise NotFoundException("Meal not found")
        return meal

    def get_meal(self, id: int, data: BaseToken):
        meal = self.get_by_id(id)
        if data.check([UserType.LLEIDAHACKER]):
            return MealGetAll.model_validate(meal)
        return MealGet.model_validate(meal)

    def add_meal(self, meal: MealCreate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to add meals")
        db_meal = Meal(**meal.model_dump())
        db.session.add(db_meal)
        db.session.commit()
        db.session.refresh(db_meal)
        return db_meal

    def update_meal(self, id: int, meal_id: int, meal: MealUpdate,
                    data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to update meals")
        db_meal = self.get_by_id(meal_id)
        set_existing_data(db_meal, meal)
        db.session.commit()
        db.session.refresh(db_meal)
        return db_meal

    def delete_meal(self, meal_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException(
                "You are not allowed to delete meals")
        db_meal = self.get_by_id(meal_id)
        db.session.delete(db_meal)
        db.session.commit()
        return db_meal

    @BaseService.needs_service(HackerService)
    @BaseService.needs_service(EventService)
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
        db.session.commit()
        db.session.refresh(event)
        return event
