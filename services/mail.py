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

from models.User import User as ModelUser


class EmailSchema(BaseModel):
    email: List[EmailStr]

FRONT_LINK = Configuration.get('OTHERS', 'FRONT_LINK')
CONTACT_MAIL = Configuration.get('MAIL', 'MAIL_FROM')

def send_email(email: str, template: str, subject: str):
    msg = MIMEText(template, "html")
    msg['Subject'] = subject
    msg['From'] = Configuration.get('MAIL', 'MAIL_FROM')
    msg['To'] = email

    try:
        with SMTP_SSL(Configuration.get('MAIL', 'MAIL_SERVER'),
                      Configuration.get('MAIL', 'MAIL_PORT')) as server:
            server.login(Configuration.get('MAIL', 'MAIL_USERNAME'),
                         Configuration.get('MAIL', 'MAIL_PASSWORD'))
            server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email],
                            msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from string import Template


def generate_registration_confirmation_template(user: ModelUser):
    t = Template(open('mail_templates/registration_confirmation.html', 'r', encoding='utf-8').read())
    return t.substitute(
        name=user.name, 
        email=user.email, 
        front_link=FRONT_LINK, 
        token=user.verification_token, 
        contact_mail=CONTACT_MAIL)

def generate_password_reset_template(user: ModelUser):
    t = Template(open('mail_templates/password_reset.html', 'r', encoding='utf-8').read())
    return t.substitute(
        name=user.name, 
        email=user.email, 
        front_link=FRONT_LINK, 
        token=user.rest_password_token, 
        contact_mail=CONTACT_MAIL)

async def send_registration_confirmation_email(user: ModelUser):
    send_email(user.email, generate_registration_confirmation_template(user), 'Registration Confirmation')

