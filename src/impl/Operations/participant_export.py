"""Event export using registration snapshots and effective attendance/meal records."""

from collections import defaultdict

from sqlalchemy import select

from src.impl.Event.model import HackerParticipation, HackerRegistration
from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
from src.impl.Meal.model import HackerMeal, Meal
from src.impl.Operations.model import ScanRecord

REGISTRATION_FIELDS = (
    "shirt_size",
    "food_restrictions",
    "description",
    "github",
    "linkedin",
    "studies",
    "study_center",
    "location",
    "how_did_you_meet_us",
    "wants_credit",
    "ticket_sent_at",
    "cancelled_at",
)


def participant_export(session, event_id, participants):
    registrations = {
        row.user_id: dict(row._mapping)
        for row in session.execute(
            select(
                HackerRegistration.user_id,
                *(getattr(HackerRegistration, field) for field in REGISTRATION_FIELDS),
            ).where(HackerRegistration.event_id == event_id)
        )
    }
    checked = set(
        session.scalars(
            select(HackerParticipation.user_id).where(
                HackerParticipation.event_id == event_id
            )
        )
    )
    meals = [
        dict(row._mapping)
        for row in session.execute(
            select(Meal.id, Meal.name)
            .where(Meal.event_id == event_id)
            .order_by(Meal.id)
        )
    ]
    # Union preserves old deliveries without counting repeated rounds twice.
    legacy = (
        select(HackerMeal.user_id, HackerMeal.meal_id)
        .join(Meal, Meal.id == HackerMeal.meal_id)
        .where(Meal.event_id == event_id)
    )
    eaten = defaultdict(set)
    for user_id, meal_id in session.execute(legacy):
        eaten[user_id].add(meal_id)
    meal_ids = {str(meal["id"]): meal["id"] for meal in meals}
    for user_id, target in session.execute(
        select(ScanRecord.user_id, ScanRecord.target).where(
            ScanRecord.event_id == event_id,
            ScanRecord.kind == "meal",
            ScanRecord.voided.is_(False),
        )
    ):
        if target in meal_ids:
            eaten[user_id].add(meal_ids[target])
    teams = defaultdict(list)
    for user_id, name in session.execute(
        select(HackerGroupUser.hacker_id, HackerGroup.name)
        .join(HackerGroup, HackerGroup.id == HackerGroupUser.group_id)
        .where(HackerGroup.event_id == event_id)
        .order_by(HackerGroup.id)
    ):
        teams[user_id].append(name)
    return {
        "meals": meals,
        "participants": [
            {
                **participant,
                **{
                    field: registrations[participant["id"]][field]
                    for field in REGISTRATION_FIELDS
                },
                "checked_in": participant["id"] in checked,
                "teams": teams[participant["id"]],
                "eaten_meal_ids": sorted(eaten[participant["id"]]),
            }
            for participant in sorted(participants, key=lambda row: row["id"])
        ],
    }
