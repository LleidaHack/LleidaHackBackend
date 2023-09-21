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

from models.User import User as ModelUser
from string import Template


class EmailSchema(BaseModel):
    email: List[EmailStr]


FRONT_LINK = Configuration.get('OTHERS', 'FRONT_URL')
CONTACT_MAIL = Configuration.get('MAIL', 'MAIL_FROM')
STATIC_FOLDER = Configuration.get(
    'OTHERS', 'FRONT_URL') + '/' + Configuration.get('OTHERS', 'STATIC_FOLDER')

def get_all_images():
    import os
    images = []
    for root, dirs, files in os.walk("mail_templates/images"):
        for file in files:
            if file.endswith(".png"):
                images.append(os.path.join(root, file))
    return images

def send_email(email: str, template: str, subject: str, attachments: List = []):
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
            # Attach parts into message container.
            msg.attach(html)
            while(attachments):
                add_image_attachment(msg, attachments.pop())
            server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email],
                            msg.as_string())
            # server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email],
                            # msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def add_image_attachment(msg, image_path):
    with open(image_path, 'rb') as f:
        img_data = f.read()
        msg.add_header('Content-ID', '<{}>'.format(image_path.split('/')[-1]))
        msg.attach(MIMEImage(img_data, 'png'))


def generate_registration_confirmation_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_registre.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        token=user.verification_token,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


def generate_password_reset_template(user: ModelUser):
    t = Template(
        open('mail_templates/forgot_password.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        token=user.rest_password_token,
                        contact_mail=CONTACT_MAIL)


async def send_registration_confirmation_email(user: ModelUser):
    send_email(user.email, generate_registration_confirmation_template(user),
               'Registration Confirmation', get_all_images())


async def send_password_reset_email(user: ModelUser):
    send_email(user.email, generate_password_reset_template(user),
               'Password Reset')


async def send_event_registration_email(user: ModelUser, event_name: str):
    pass


async def send_event_accepted_email(user: ModelUser, event_name: str):
    pass


# async def send_event_rejected_email(user: ModelUser, event_name: str):
#     pass


async def send_dailyhack_added_email(user: ModelUser, dailyhack_name: str):
    pass


async def send_contact_email(name: str, title: str, email: str, message: str):
    pass
