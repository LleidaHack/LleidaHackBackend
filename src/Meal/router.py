from database import get_db
from security import get_data_from_token

from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter
from utils.auth_bearer import JWTBearer
from src.Meal.schema import Meal as SchemaMeal

import src.Meal.service as meal_service

router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
)


@router.get("/{id}/all")
async def get_meals(id: int,
                    db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    return await meal_service.get_meals(id, db, get_data_from_token(token))


@router.get("/{id}/{meal_id}")
async def get_meal(id: int,
                   meal_id: int,
                   db: Session = Depends(get_db),
                   token: str = Depends(JWTBearer())):
    return await meal_service.get_meal(id, meal_id, db,
                                       get_data_from_token(token))


@router.post("/")
async def create_meal(meal: SchemaMeal,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return await meal_service.add_meal(meal, db, get_data_from_token(token))


@router.put("/{id}/{meal_id}")
async def update_meal(id: int,
                      meal_id: int,
                      meal: SchemaMeal,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return await meal_service.update_meal(id, meal_id, meal, db,
                                          get_data_from_token(token))


@router.delete("/{id}/{meal_id}")
async def delete_meal(id: int,
                      meal_id: int,
                      db: Session = Depends(get_db),
                      token: str = Depends(JWTBearer())):
    return await meal_service.delete_meal(id, meal_id, db,
                                          get_data_from_token(token))
