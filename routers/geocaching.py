from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends, Response
from database import get_db
from services import geocaching as geocaching_service

router = APIRouter()


@router.get("/geocaching")
async def get_all_geocachings():
    # return geocaching_service
    pass


@router.get("/geocaching/{code}")
async def get_geocaching(code: str):
    # Your code here
    pass


@router.get("/geocaching/hacker/{user_code}")
async def get_all_hacker_geocaching(user_code: str,
                                    db: Session = Depends(get_db)):
    return geocaching_service.get_all_hacker_geocaching(db, user_code)


@router.post("/geocaching/hacker/{user_code}/{code}")
async def add_user_geocaching(user_code: str,
                              code: str,
                              db: Session = Depends(get_db)):
    return geocaching_service.add_user_geocaching(db, user_code, code)


@router.put("/geocaching/hacker/{user_code}")
async def claim_lleidacoins(user_code: str, db: Session = Depends(get_db)):
    return geocaching_service.claim_lleidacoins(db, user_code)
