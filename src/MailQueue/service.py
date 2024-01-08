from ast import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from fastapi import HTTPException
from sqlalchemy.orm import Session
from config import Configuration
from error.AuthenticationException import AuthenticationException

from src.Utils import TokenData
from src.User.model import User as ModelUser
from src.MailQueue.model import MailQueue as ModelMailQueue

FRONT_LINK = Configuration.get('OTHERS', 'FRONT_URL')
BACK_LINK = Configuration.get('OTHERS', 'BACK_URL')
CONTACT_MAIL = Configuration.get('OTHERS', 'CONTACT_MAIL')
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


def set_sent(mail, db: Session):
    mail.sent = True
    db.commit()


async def get_last(db: Session, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    return db.query(ModelMailQueue).filter(
        ModelMailQueue.sent == False).order_by(
            ModelMailQueue.id.asc()).first()


async def get_by_id(db: Session, id: int, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    return db.query(ModelMailQueue).filter(ModelMailQueue.id == id).first()


async def count_unsent(db: Session, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    unsent_count = db.query(ModelMailQueue).filter(
        ModelMailQueue.sent == False).count()
    return unsent_count


async def clear_queue(db: Session, data: TokenData):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    db.query(ModelMailQueue).delete()
    db.commit()
