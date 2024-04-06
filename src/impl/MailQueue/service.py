from ast import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.error.AuthenticationException import AuthenticationException
from src.impl.MailQueue.model import MailQueue as ModelMailQueue
from src.utils.Token import BaseToken



def send_email(email: str,
               template: str,
               subject: str,
               attachments: List = []):
    pass
    # msg = MIMEMultipart('related')
    # msg['Subject'] = subject
    # msg['From'] = Configuration.get('MAIL', 'MAIL_FROM')
    # msg['To'] = email

    # try:
    #     with SMTP_SSL(Configuration.get('MAIL', 'MAIL_SERVER'),
    #                   Configuration.get('MAIL', 'MAIL_PORT')) as server:
    #         server.login(Configuration.get('MAIL', 'MAIL_USERNAME'),
    #                      Configuration.get('MAIL', 'MAIL_PASSWORD'))
    #         #send multipart mail adding images withn add_image_attachment and the html
    #         html = MIMEText(template, 'html')
    #         msg.attach(html)
    #         server.sendmail(Configuration.get('MAIL', 'MAIL_FROM'), [email],
    #                         msg.as_string())
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


def set_sent(mail, db: Session):
    mail.sent = True
    db.commit()


def get_last(db: Session, data: BaseToken):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    return db.query(ModelMailQueue).filter(
        ModelMailQueue.sent == False).order_by(
            ModelMailQueue.id.asc()).first()


def get_by_id(db: Session, id: int, data: BaseToken):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    return db.query(ModelMailQueue).filter(ModelMailQueue.id == id).first()


def count_unsent(db: Session, data: BaseToken):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    unsent_count = db.query(ModelMailQueue).filter(
        ModelMailQueue.sent == False).count()
    return unsent_count


def clear_queue(db: Session, data: BaseToken):
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    db.query(ModelMailQueue).delete()
    db.commit()
