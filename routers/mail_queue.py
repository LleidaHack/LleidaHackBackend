from sqlalchemy.orm import Session
from fastapi import Depends, Response, APIRouter

from database import get_db
from error.AuthenticationException import AuthenticationException
from security import get_data_from_token
import services.mail_queue as mail_queue_service
from utils.auth_bearer import JWTBearer

from schemas.User import User as SchemaUser

router = APIRouter(
    prefix="/mail_queue",
    tags=["MailQueue"],
)


@router.post("/send_mail")
async def send_mail(db: Session = Depends(get_db),
                    token: str = Depends(JWTBearer())):
    """
    Send a mail to all users
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    mail = mail_queue_service.get_last(db, data)
    return mail
    # send
    mail_queue_service.send_email(mail.user.email, mail.body, mail.subject)
    mail_queue_service.set_sent(mail, db)
    return await mail_queue_service.count_unsent(db, data)


@router.post("/send_mail_by_id")
async def send_mail_by_id(id: int,
                          db: Session = Depends(get_db),
                          token: str = Depends(JWTBearer())):
    """
    Send a mail to all users
    """
    data = get_data_from_token(token)
    if not data.is_admin:
        raise AuthenticationException("Not authorized")
    mail = await mail_queue_service.get_by_id(id)
    # send
    mail_queue_service.send_email(mail.user.email, mail.body, mail.subject)
    mail_queue_service.set_sent(mail, db)
    return mail_queue_service.count_unsent(db, data)

@router.get("count")
async def count(db: Session = Depends(get_db), token: str = Depends(JWTBearer())):
    return await mail_queue_service.count_unsent(db, get_data_from_token(token))
