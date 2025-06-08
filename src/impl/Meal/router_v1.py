from fastapi import APIRouter

from src.impl.Meal.schema import MealCreate, MealGet, MealGetAll, MealUpdate
from src.impl.Meal.service import MealService
from src.utils.jwt_bearer import jwt_dependency
from src.utils.token import BaseToken

router = APIRouter(
    prefix='/meal',
    tags=['Meal'],
)

meal_service = MealService()


@router.get('/{event_id}/all', response_model=list[MealGet])
def get_all(event_id: int, token: BaseToken = jwt_dependency):
    return meal_service.get_all(event_id)


@router.get('/{meal_id}', response_model=MealGetAll | MealGet)
def get(meal_id: int, token: BaseToken = jwt_dependency):
    return meal_service.get_meal(meal_id, token)


@router.post('/')
def create(meal: MealCreate, token: BaseToken = jwt_dependency):
    return meal_service.add_meal(meal, token)


@router.put('/{event_id}/{meal_id}')
def update(
    event_id: int, meal_id: int, meal: MealUpdate, token: BaseToken = jwt_dependency
):
    return meal_service.update_meal(event_id, meal_id, meal, token)


@router.delete('/{meal_id}')
def delete(meal_id: int, token: BaseToken = jwt_dependency):
    return meal_service.delete_meal(meal_id, token)


@router.put('/{meal_id}/eat/{hacker_code}')
def eat(meal_id: int, hacker_code: str, token: BaseToken = jwt_dependency):
    """
    Register a hacker to an event
    """
    return meal_service.eat(meal_id, hacker_code, token)
