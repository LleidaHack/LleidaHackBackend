from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
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
from string import Template

from models.User import User as ModelUser
from models.Event import Event as ModelEvent


class EmailSchema(BaseModel):
    email: List[EmailStr]


FRONT_LINK = Configuration.get('OTHERS', 'FRONT_URL')
BACK_LINK = Configuration.get('OTHERS', 'BACK_URL')
CONTACT_MAIL = Configuration.get('MAIL', 'MAIL_FROM')
STATIC_FOLDER = Configuration.get('OTHERS',
                                  'BACK_URL') + '/' + Configuration.get(
                                      'OTHERS', 'STATIC_FOLDER') + '/images'


def send_email(email: str,
               template: str,
               subject: str,
               attachments: List = []):
    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = Configuration.get('MAIL', 'MAIL_FROM')
    msg['To'] = email

    try:
        with SMTP_SSL(Configuration.get('MAIL', 'MAIL_SERVER'),
                      Configuration.get('MAIL', 'MAIL_PORT')) as server:
            server.login(Configuration.get('MAIL', 'MAIL_USERNAME'),
                         Configuration.get('MAIL', 'MAIL_PASSWORD'))
            #send multipart mail adding images withn add_image_attachment and the html
            html = MIMEText(template, 'html')
            msg.attach(html)
            server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email],
                            msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_registration_confirmation_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_registre.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        days_left=5,
                        front_link=FRONT_LINK,
                        token=user.verification_token,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


async def send_registration_confirmation_email(user: ModelUser):
    send_email(user.email, generate_registration_confirmation_template(user),
               'Registration Confirmation')


def generate_password_reset_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_reset_password.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        token=user.rest_password_token,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


async def send_password_reset_email(user: ModelUser):
    send_email(user.email, generate_password_reset_template(user),
               'Password Reset')


def generate_event_registration_template(user: ModelUser, event_name: str):
    t = Template(
        open('mail_templates/correu_inscripcio_hackeps.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(
        name=user.name,
        email=user.email,
        event_name=event_name,
        # token=user.verification_token,
        front_link=FRONT_LINK,
        contact_mail=CONTACT_MAIL,
        static_folder=STATIC_FOLDER)


async def send_event_registration_email(user: ModelUser, event: ModelEvent):
    send_email(user.email, generate_event_registration_template(user, event),
               'Event Registration')


def generate_event_accepted_template(user: ModelUser, event: ModelEvent,
                                     token: str):
    t = Template(
        open('mail_templates/correu_acceptacio_event.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        event_name=event.name,
                        days_left=5,
                        token=token,
                        back_link=BACK_LINK,
                        front_link=FRONT_LINK,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


async def send_event_accepted_email(user: ModelUser, event: ModelEvent,
                                    token: str):
    send_email(user.email,
               generate_event_accepted_template(user, event,
                                                token), 'Event Accepted')


def generate_dailyhack_entregat_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_entrega_dailyhack.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


async def send_dailyhack_added_email(user: ModelUser):
    send_email(user.email, generate_dailyhack_entregat_template(user),
               'Dailyhack Entregat')


# def generate_dailyhack_publicat_template(user: ModelUser, dailyhack_name: str):
#     t = Template(
#         open('mail_templates/correu_publicacio_dailyhack.html',
#              'r',
#              encoding='utf-8').read())
#     return t.substitute(name=user.name,
#                         email=user.email,
#                         dailyhack_name=dailyhack_name,
#                         front_link=FRONT_LINK,
#                         contact_mail=CONTACT_MAIL,
#                         static_folder=STATIC_FOLDER)


def generate_contact_template(name: str, title: str, email: str, message: str):
    t = Template(
        open('mail_templates/correu_contacte.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=name,
                        email=email,
                        title=title,
                        message=message,
                        static_folder=STATIC_FOLDER)


async def send_contact_email(name: str, title: str, email: str, message: str):
    send_email(CONTACT_MAIL,
               generate_contact_template(name, title, email, message), title)


# async def send_event_rejected_email(user: ModelUser, event_name: str):
#     pass
