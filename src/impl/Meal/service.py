from fastapi_sqlalchemy import db

from src.error.AuthenticationException import AuthenticationException
from src.error.InvalidDataException import InvalidDataException
from src.error.NotFoundException import NotFoundException
from src.impl.Event.service import EventService
from src.impl.Hacker.service import HackerService
from src.impl.Meal.model import Meal
from src.impl.Meal.schema import MealCreate, MealGet, MealGetAll, MealUpdate
from src.utils.Base.BaseService import BaseService
from src.utils.service_utils import set_existing_data
from src.utils.Token import BaseToken
from src.utils.UserType import UserType


class MealService(BaseService):
    name = "meal_service"
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

    def update_meal(self, id: int, meal_id: int, meal: MealUpdate, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to update meals")
        db_meal = self.get_by_id(meal_id)
        set_existing_data(db_meal, meal)
        db.session.commit()
        db.session.refresh(db_meal)
        return db_meal

    def delete_meal(self, meal_id: int, data: BaseToken):
        if not data.check([UserType.LLEIDAHACKER]):
            raise AuthenticationException("You are not allowed to delete meals")
        db_meal = self.get_by_id(meal_id)
        db.session.delete(db_meal)
        db.session.commit()
        return db_meal

    @BaseService.needs_service(HackerService)
    @BaseService.needs_service(EventService)
    def eat(self, meal_id: int, hacker_code: str, data: BaseToken):
        # Preserve the legacy route while applying the same audit and round rules.
        from uuid import uuid4

        from src.impl.Operations.schema import Operation
        from src.impl.Operations.service import perform, state
        from src.utils.access import access_role

        event_id = self.get_by_id(meal_id).event_id
        _, row = state(event_id)
        current_round = (
            (row.config or {})
            .get("meal_rounds", {})
            .get(str(meal_id), {})
            .get("round", 1)
        )
        result = perform(
            event_id,
            Operation(
                operation_id=uuid4(),
                kind="meal",
                code=hacker_code,
                target=str(meal_id),
                round=current_round,
                device="legacy-meal-api",
            ),
            data,
            # Gestió's manual "register meal by code" uses ticket codes; scanner
            # volunteers (lleidahacker) must still scan the physical badge.
            allow_ticket_meal=access_role(data) in {"superadmin", "admin"},
        )
        if not result["ok"]:
            if result["status"] == 404:
                raise NotFoundException(result["error"])
            if result["status"] == 403:
                raise AuthenticationException(result["error"])
            raise InvalidDataException(result["error"])
        return self.event_service.get_by_id(self.get_by_id(meal_id).event_id)
