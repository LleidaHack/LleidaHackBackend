from enum import Enum


class InternalTemplate(Enum):
    USER_CREATED = 'user_created'
    CONTACT = 'contact'
    RESET_PASSWORD = 'reset_password'

    EVENT_REGISTRATION_REMINDER = 'event_registration_reminder'

    EVENT_HACKER_REGISTERED = 'event_hacker_registered'
    EVENT_HACKER_ACCEPTED = 'event_hacker_accepted'
    # EVENT_HACKER_REJECTED = 'event_hacker_accepted'
    # EVENT_HACKER_CONFIRMATION = 'event_hacker_confirmation'
