from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

import src.impl.MailQueue.service as mail_queue_service
from src.error.AuthenticationException import AuthenticationException
from src.impl.User.schema import UserGet as SchemaUser
from src.utils.database import Database
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/mail_queue",
    tags=["MailQueue"],
)


@router.post("/send_mail")
def send_mail(db: Session = Depends(Database.get_db),
              token: BaseToken = Depends(JWTBearer())):
    """
    Send a mail to all users
    """
    if not token.is_admin:
        raise AuthenticationException("Not authorized")
    mail = mail_queue_service.get_last(db, token)
    # send
    if mail is None:
        raise Exception("No mail to send")
    mail_queue_service.send_email(mail.user.email, mail.body, mail.subject)
    mail_queue_service.set_sent(mail, db)
    return mail_queue_service.count_unsent(db, token)


@router.post("/send_mail_by_id")
def send_mail_by_id(id: int,
                    db: Session = Depends(Database.get_db),
                    token: BaseToken = Depends(JWTBearer())):
    """
    Send a mail to all users
    """
    if not token.is_admin:
        raise AuthenticationException("Not authorized")
    mail = mail_queue_service.get_by_id(id)
    return mail
    # send
    mail_queue_service.send_email(mail.user.email, mail.body, mail.subject)
    mail_queue_service.set_sent(mail, db)
    return mail_queue_service.count_unsent(db, data)


@router.get("/count")
def count(db: Session = Depends(Database.get_db),
          token: BaseToken = Depends(JWTBearer())):
    return mail_queue_service.count_unsent(db, token)


@router.post("/clear_queue")
def clear_queue(db: Session = Depends(Database.get_db),
                token: BaseToken = Depends(JWTBearer())):
    """
    Clear the mail queue
    """
    if not token.is_admin:
        raise AuthenticationException("Not authorized")
    mail_queue_service.clear_queue(db, token)
    return {"message": "Mail queue cleared"}
