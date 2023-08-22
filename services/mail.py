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

def send_email(email: str, template: str):
    msg = MIMEText(template, "html")
    msg['Subject'] = "Test Email"
    msg['From'] = Configuration.get('MAIL', 'MAIL_FROM')
    msg['To'] = email

    try:
        with SMTP_SSL(Configuration.get('MAIL', 'MAIL_SERVER'), Configuration.get('MAIL', 'MAIL_PORT')) as server:
            server.login(Configuration.get('MAIL', 'MAIL_USERNAME'), Configuration.get('MAIL', 'MAIL_PASSWORD'))
            server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email], msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
