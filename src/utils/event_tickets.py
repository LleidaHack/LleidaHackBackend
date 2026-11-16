"""One eligibility policy for ticket recipients, downloads and Wallet passes."""

from src.impl.Event.model import EventTicketDelivery, HackerRegistration
from src.impl.Operations.model import EventMentor
from src.impl.User.model import User

STAFF_ROLES = frozenset({"lleidahacker", "admin", "superadmin"})


def ticket_role(session, event, user):
    if user is None or user.is_deleted or not user.code:
        return None
    if user.access_role in STAFF_ROLES:
        return "Staff"
    if user.access_role == "mentor":
        entry = session.get(EventMentor, (event.id, user.id))
        return "Mentor" if entry and entry.active else None
    if user.access_role == "hacker" and user in event.accepted_hackers:
        registration = session.get(HackerRegistration, (user.id, event.id))
        if registration and registration.confirmed_assistance:
            return "Hacker"
    return None


def eligible_tickets(session, event):
    """Return user/state/role without creating delivery rows during reads."""
    mentors = session.query(EventMentor.user_id).filter_by(
        event_id=event.id, active=True
    )
    candidates = {user.id: user for user in event.accepted_hackers}
    for user in session.query(User).filter(
        (User.access_role.in_(STAFF_ROLES)) | (User.id.in_(mentors))
    ):
        candidates[user.id] = user
    for user in candidates.values():
        role = ticket_role(session, event, user)
        if role is None:
            continue
        delivery = session.get(EventTicketDelivery, (event.id, user.id))
        # Preserve delivery history of existing participant tickets.
        if delivery is None and role == "Hacker":
            delivery = session.get(HackerRegistration, (user.id, event.id))
        yield user, delivery, role


def ticket_email(session, event, user):
    if user.access_role == "mentor":
        entry = session.get(EventMentor, (event.id, user.id))
        return (
            entry.invitation_email
            if entry and entry.invitation_email is not None
            else user.email
        )
    return user.email
