from typing import List, Union
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from database import get_db
from security import get_data_from_token
from utils.auth_bearer import JWTBearer

import src.Meal.service as meal_service

from Meal.schema import MealGet as MealGetSchema
from Meal.schema import MealGetAll as MealGetAllSchema
from Meal.schema import MealCreate as MealCreateSchema
from Meal.schema import MealUpdate as MealUpdateSchema


router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
)


@router.get("/{id}/all", response_model=List[MealGetSchema])
def get_meals(id: int,
                    db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return meal_service.get_meals(id, db, get_data_from_token(token))


@router.get("/{id}/{meal_id}", response_model=Union[MealGetSchema, MealGetAllSchema])
def get_meal(id: int,
                   db: Session = Depends(get_db),
                   token: str = Depends(JWTBearer())):
    return meal_service.get_meal(id, db,
                                       get_data_from_token(token))


@router.post("/")
def create_meal(meal: MealCreateSchema,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return meal_service.add_meal(meal, db, get_data_from_token(token))


@router.put("/{id}/{meal_id}")
def update_meal(id: int,
                      meal_id: int,
                      meal: MealUpdateSchema,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return meal_service.update_meal(id, meal_id, meal, db,
                                          get_data_from_token(token))


@router.delete("/{id}/{meal_id}")
def delete_meal(id: int,
                      meal_id: int,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return meal_service.delete_meal(id, meal_id, db,
                                          get_data_from_token(token))
