from fastapi import APIRouter

from src.impl.Geocaching import service as geocaching_service

router = APIRouter()


@router.get('/geocaching')
def get_all_geocachings():
    # return geocaching_service
    return 'UNAVALIABLE'


@router.get('/geocaching/{code}')
def get_geocaching(code: str):
    # Your code here
    return 'UNAVALIABLE'


@router.get('/geocaching/hacker/{user_code}')
def get_all_hacker_geocaching(user_code: str):
    return geocaching_service.get_all_hacker_geocaching(user_code)


@router.post('/geocaching/hacker/{user_code}/{code}')
def add_user_geocaching(user_code: str, code: str):
    return geocaching_service.add_user_geocaching(user_code, code)


@router.put('/geocaching/hacker/{user_code}')
def claim_lleidacoins(user_code: str):
    return geocaching_service.claim_lleidacoins(user_code)
