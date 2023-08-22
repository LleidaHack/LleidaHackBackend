from config import Configuration
from fastapi import FastAPI
from starlette.responses import JSONResponse
from pydantic import EmailStr, BaseModel
from typing import List
from models.UserType import UserType
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from smtplib import SMTP_SSL
from email.mime.text import MIMEText


class EmailSchema(BaseModel):
    email: List[EmailStr]


# conf = ConnectionConfig(
#     MAIL_USERNAME = Configuration.get('MAIL', 'MAIL_USERNAME'),
#     MAIL_PASSWORD = Configuration.get('MAIL', 'MAIL_PASSWORD'),
#     MAIL_FROM = Configuration.get('MAIL', 'MAIL_FROM'),
#     MAIL_PORT = int(Configuration.get('MAIL', 'MAIL_PORT')),
#     MAIL_SERVER = Configuration.get('MAIL', 'MAIL_SERVER'),
#     MAIL_FROM_NAME = Configuration.get('MAIL', 'MAIL_FROM_NAME'),
#     MAIL_TLS = True,
#     MAIL_SSL = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )

app = FastAPI()

html = """<p>Hi this test mail, thanks for using Fastapi-mail</p> """


async def simple_send(email: EmailSchema):
    pass