"""ECTS applicants and their team's recorded presentation status."""

from sqlalchemy import select

from src.impl.Event.model import HackerRegistration
from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
from src.impl.Operations.model import Presentation
from src.impl.User.model import User


def credit_participants(session, event_id: int):
    presented = (
        select(Presentation.id)
        .join(HackerGroup, HackerGroup.id == Presentation.group_id)
        .join(HackerGroupUser, HackerGroupUser.group_id == HackerGroup.id)
        .where(
            HackerGroupUser.hacker_id == User.id,
            HackerGroup.event_id == event_id,
            Presentation.event_id == event_id,
            Presentation.state == "done",
        )
        .exists()
    )
    rows = session.execute(
        select(User.name, User.email, presented.label("team_presented"))
        .join(HackerRegistration, HackerRegistration.user_id == User.id)
        .where(
            HackerRegistration.event_id == event_id,
            HackerRegistration.wants_credit.is_(True),
        )
        .order_by(User.name, User.email, User.id)
    )
    return [dict(row._mapping) for row in rows]
