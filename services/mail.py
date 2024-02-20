from config import Configuration
from pydantic import EmailStr, BaseModel
from typing import List
from database import db_get
from pydantic import BaseModel
from string import Template

from src.impl.User.model import User as ModelUser
from src.impl.Event.model import Event as ModelEvent
from src.impl.MailQueue.model import MailQueue as ModelMailQueue
from src.impl.MailQueue import service as mail_queue_service


class EmailSchema(BaseModel):
    email: List[EmailStr]


FRONT_LINK = Configuration.get('OTHERS', 'FRONT_URL')
BACK_LINK = Configuration.get('OTHERS', 'BACK_URL')
CONTACT_MAIL = Configuration.get('OTHERS', 'CONTACT_MAIL')
STATIC_FOLDER = Configuration.get('OTHERS',
                                  'BACK_URL') + '/' + Configuration.get(
                                      'OTHERS', 'STATIC_FOLDER') + '/images'


def send_bulk_mails(lst: List):
    db = db_get()
    db.bulk_save_objects(lst)
    db.commit()


def send_email(user, body: str, subject: str, queue: bool = False):
    mail = user
    if not queue:
        try:
            mail = user.email
        except:
            pass
        mail_queue_service.send_email(mail, body, subject)
    else:
        db = db_get()
        mail = ModelMailQueue()
        mail.user_id = user.id
        mail.subject = subject
        mail.body = body
        db.add(mail)
        db.commit()


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


def send_registration_confirmation_email(user: ModelUser):
    send_email(user, generate_registration_confirmation_template(user),
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


def send_password_reset_email(user: ModelUser):
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


def send_event_registration_email(user: ModelUser, event: ModelEvent):
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


def send_event_accepted_email(user: ModelUser, event: ModelEvent, token: str):
    send_email(user.email,
               generate_event_accepted_template(user, event,
                                                token), 'Event Accepted')


def generate_dailyhack_entregat_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_dailyhack_entregat.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


def send_dailyhack_added_email(user: ModelUser):
    send_email(user.email, generate_dailyhack_entregat_template(user),
               'Dailyhack Entregat')


def generate_dailyhack_obert_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_dailyhack_publicat.html',
             'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        front_link=FRONT_LINK,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


def send_dailyhack_open_email(user: ModelUser):
    send_email(user.email, generate_dailyhack_obert_template(user),
               'Dailyhack Obert', True)


def send_all_dailyhack_mails(lst: List):
    out = []
    for u in lst:
        m = ModelMailQueue()
        m.user_id = u.id
        m.subject = 'Dailyhack Obert'
        m.body = generate_dailyhack_obert_template(u)
        out.append(m)
    # return out
    send_bulk_mails(out)
    return len(out)


def generate_reminder_template(user: ModelUser):
    t = Template(
        open('mail_templates/correu_recordatory.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=user.name,
                        email=user.email,
                        front_link=FRONT_LINK,
                        contact_mail=CONTACT_MAIL,
                        static_folder=STATIC_FOLDER)


def send_reminder_email(user: ModelUser):
    send_email(user.email, generate_reminder_template(user), 'Reminder', True)


def send_all_reminder_mails(lst: List):
    out = []
    for u in lst:
        m = ModelMailQueue()
        m.user_id = u.id
        m.subject = 'Reminder'
        m.body = generate_reminder_template(u)
        out.append(m)
    # return out
    send_bulk_mails(out)
    return len(out)


def generate_contact_template(name: str, title: str, email: str, message: str):
    t = Template(
        open('mail_templates/correu_contacte.html', 'r',
             encoding='utf-8').read())
    return t.substitute(name=name,
                        email=email,
                        title=title,
                        message=message,
                        static_folder=STATIC_FOLDER)


def send_contact_email(name: str, title: str, email: str, message: str):
    send_email(CONTACT_MAIL,
               generate_contact_template(name, title, email, message), title)


# def send_event_rejected_email(user: ModelUser, event_name: str):
#     pass
