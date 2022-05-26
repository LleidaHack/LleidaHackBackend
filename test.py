from __future__ import annotations
import datetime

from fastapi import Depends, FastAPI, Response, status, Request
from fastapi.security import HTTPBearer
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# from dataclasses import dataclass
from pydantic import BaseModel

# @dataclass
class Uer(BaseModel):
    id: Optional[int]=None
    name: str
    nickname: str
    password: str
    birthdate: date
    food_restrictions: str
    email: str
    telephone: str
    address: str
    shirtSize: str

# Scheme for the Authorization header
token_auth_scheme = HTTPBearer()

app = FastAPI(title="API_NAME",
              description="API_DESC",
              version="0.2.0",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              openapi_url='/api/openapi.json')

import Models

@app.get("/")
def t():
    # return "s"
    return Models.User.init("t","t","",datetime.datetime.now(),"","","","","").name

