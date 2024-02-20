from typing import List, Union
from fastapi import Depends, APIRouter

from security import get_data_from_token
from utils.auth_bearer import JWTBearer

from src.Meal.service import MealService

from src.Meal.schema import MealGet as MealGetSchema
from src.Meal.schema import MealGetAll as MealGetAllSchema
from src.Meal.schema import MealCreate as MealCreateSchema
from src.Meal.schema import MealUpdate as MealUpdateSchema

router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
)

meal_service = MealService()

@router.get("/{id}/all", response_model=List[MealGetSchema])
def get_meals(id: int,
              token: str = Depends(JWTBearer())):
    return meal_service.get_meals(id, get_data_from_token(token))


@router.get("/{id}/{meal_id}",
            response_model=Union[MealGetSchema, MealGetAllSchema])
def get_meal(id: int,
             token: str = Depends(JWTBearer())):
    return meal_service.get_meal(id, get_data_from_token(token))


@router.post("/")
def create_meal(meal: MealCreateSchema,
                token: str = Depends(JWTBearer())):
    return meal_service.add_meal(meal, get_data_from_token(token))


@router.put("/{id}/{meal_id}")
def update_meal(id: int,
                meal_id: int,
                meal: MealUpdateSchema,
                token: str = Depends(JWTBearer())):
    return meal_service.update_meal(id, meal_id, meal, get_data_from_token(token))


@router.delete("/{id}/{meal_id}")
def delete_meal(id: int,
                meal_id: int,
                token: str = Depends(JWTBearer())):
    return meal_service.delete_meal(id, meal_id, get_data_from_token(token))
