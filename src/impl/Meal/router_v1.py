from typing import List, Union

from fastapi import APIRouter, Depends

from src.impl.Meal.schema import MealCreate
from src.impl.Meal.schema import MealGet
from src.impl.Meal.schema import MealGetAll
from src.impl.Meal.schema import MealUpdate
from src.impl.Meal.service import MealService
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
)

meal_service = MealService()


@router.get("/{id}/all", response_model=List[MealGet])
def get_all(id: int, token: BaseToken = Depends(JWTBearer())):
    return meal_service.get_all(id)


@router.get("/{id}", response_model=Union[MealGetAll, MealGet])
def get(id: int, token: BaseToken = Depends(JWTBearer())):
    return meal_service.get_meal(id, token)


@router.post("/")
def create(meal: MealCreate, token: BaseToken = Depends(JWTBearer())):
    return meal_service.add_meal(meal, token)


@router.put("/{id}/{meal_id}")
def update(id: int,
           meal_id: int,
           meal: MealUpdate,
           token: BaseToken = Depends(JWTBearer())):
    return meal_service.update_meal(id, meal_id, meal, token)


@router.delete("/{id}")
def delete(id: int, token: BaseToken = Depends(JWTBearer())):
    return meal_service.delete_meal(id, token)


@router.put("/{meal_id}/eat/{hacker_code}")
def eat(meal_id: int,
        hacker_code: str,
        token: BaseToken = Depends(JWTBearer())):
    """
    Register a hacker to an event
    """
    return meal_service.eat(meal_id, hacker_code, token)
