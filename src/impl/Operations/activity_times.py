"""Internal activity results derived from immutable, idempotent scan attempts."""

from fastapi import HTTPException
from fastapi_sqlalchemy import db
from sqlalchemy import func

from src.impl.Operations.model import OperationAudit
from src.impl.User.model import User


def ranking(event_id, activity_id, config):
    activity = next(
        (a for a in config.get("activities", []) if a["id"] == activity_id), None
    )
    if not activity:
        raise HTTPException(404, "Activity not found")
    duration = OperationAudit.details["duration_ms"].as_integer()
    best = func.max(duration).label("best_duration_ms")
    rows = (
        db.session.query(
            User.id, User.name, best, func.count(OperationAudit.id).label("attempts")
        )
        .join(OperationAudit, OperationAudit.user_id == User.id)
        .filter(
            OperationAudit.event_id == event_id,
            OperationAudit.action == "activity",
            OperationAudit.outcome == "success",
            OperationAudit.details["target"].as_string() == activity_id,
            duration > 0,
        )
        .group_by(User.id, User.name)
        .order_by(best.desc(), User.name, User.id)
        .all()
    )
    result, previous, rank = [], None, 0
    for position, row in enumerate(rows, 1):
        if row.best_duration_ms != previous:
            rank = position
        previous = row.best_duration_ms
        result.append(
            {
                "rank": rank,
                "user_id": row.id,
                "name": row.name,
                "best_duration_ms": row.best_duration_ms,
                "attempts": row.attempts,
            }
        )
    return {"activity": activity["title"], "participants": result}


def guesses(event_id, activity_id, config):
    """Latest amount each person said in a «Compta LleidaCoins» activity."""
    activity = next(
        (a for a in config.get("activities", []) if a["id"] == activity_id), None
    )
    if not activity:
        raise HTTPException(404, "Activity not found")
    rows = (
        db.session.query(
            User.id,
            User.name,
            OperationAudit.details["guess"].as_integer().label("guess"),
            OperationAudit.created_at,
        )
        .join(OperationAudit, OperationAudit.user_id == User.id)
        .filter(
            OperationAudit.event_id == event_id,
            OperationAudit.action == "activity",
            OperationAudit.outcome == "success",
            OperationAudit.details["target"].as_string() == activity_id,
            OperationAudit.details["guess"].as_integer().isnot(None),
        )
        .order_by(OperationAudit.id)
        .all()
    )
    # A later scan of the same person corrects the earlier guess.
    latest = {}
    for row in rows:
        previous = latest.get(row.id)
        latest[row.id] = {
            "user_id": row.id,
            "name": row.name,
            "guess": row.guess,
            "scanned_at": row.created_at.isoformat(),
            "scans": (previous["scans"] if previous else 0) + 1,
        }
    return {
        "activity": activity["title"],
        "participants": sorted(
            latest.values(), key=lambda p: (-p["guess"], p["scanned_at"])
        ),
    }
