from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Meal.schema import MealCreate as MealCreateSchema
from src.impl.Meal.schema import MealGet as MealGetSchema
from src.impl.Meal.schema import MealGetAll as MealGetAllSchema
from src.impl.Meal.schema import MealUpdate as MealUpdateSchema
from src.impl.Meal.service import MealService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
)

meal_service = MealService()


@router.get("/{id}/all", response_model=List[MealGetSchema])
def get_meals(id: int, token: BaseToken = Depends(JWTBearer())):
    return meal_service.get_all(id)


@router.get("/{id}",
            response_model=Union[MealGetAllSchema, MealGetSchema])
def get_meal(id: int, token: BaseToken = Depends(JWTBearer())):
    return meal_service.get_meal(id, token)


@router.post("/")
def create_meal(meal: MealCreateSchema,
                token: BaseToken = Depends(JWTBearer())):
    return meal_service.add_meal(meal, token)


@router.put("/{id}/{meal_id}")
def update_meal(id: int,
                meal_id: int,
                meal: MealUpdateSchema,
                token: BaseToken = Depends(JWTBearer())):
    return meal_service.update_meal(id, meal_id, meal, token)


@router.delete("/{id}/{meal_id}")
def delete_meal(id: int, meal_id: int,
                token: BaseToken = Depends(JWTBearer())):
    return meal_service.delete_meal(id, meal_id, token)


@router.put("/{meal_id}/eat/{hacker_code}")
def eat(meal_id: int,
        hacker_code: str,
        token: BaseToken = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    return meal_service.eat(meal_id, hacker_code, token)
