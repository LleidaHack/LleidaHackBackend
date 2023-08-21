from database import get_db
from security import oauth_schema, get_data_from_token

from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from security import check_permissions

# from schemas.Event import Event as SchemaEvent
from schemas.Meal import Meal as SchemaMeal


# from models.Event import Event as ModelEvent
# from models.Company import Company as ModelCompany
# from models.Hacker import Hacker as ModelHacker
# from models.Hacker import HackerGroup as ModelHackerGroup

import services.meal as meal_service

router = APIRouter(
    prefix="/meal",
    tags=["Meal"],
    # dependencies=[Depends(get_db)],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


@router.get("/{id}/all")
async def get_meals(id: int,
                    db: Session = Depends(get_db),
                    token: str = Depends(oauth_schema)):
    return await meal_service.get_meals(id, db, get_data_from_token(token))

@router.get("/{id}/{meal_id}")
async def get_meal(id: int,
                   meal_id: int,
                   db: Session = Depends(get_db),
                   token: str = Depends(oauth_schema)):
    return await meal_service.get_meal(id, meal_id, db, get_data_from_token(token))

@router.post("/")
async def create_meal(meal: SchemaMeal,
                        db: Session = Depends(get_db),
                        token: str = Depends(oauth_schema)):
    return await meal_service.add_meal(meal, db, get_data_from_token(token))

@router.put("/{id}/{meal_id}")
async def update_meal(id: int,
                      meal_id: int,
                      meal: SchemaMeal,
                      db: Session = Depends(get_db),
                      token: str = Depends(oauth_schema)):
    return await meal_service.update_meal(id, meal_id, meal, db, get_data_from_token(token))

@router.delete("/{id}/{meal_id}")
async def delete_meal(id: int,
                        meal_id: int,
                        db: Session = Depends(get_db),
                        token: str = Depends(oauth_schema)):
        return await meal_service.delete_meal(id, meal_id, db, get_data_from_token(token))