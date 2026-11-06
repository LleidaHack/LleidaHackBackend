"""Event-scoped operations with atomic audit, replay protection and row locking."""

import hashlib
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from fastapi_sqlalchemy import db
from sqlalchemy import case, func

from src.impl.Event.model import Event
from src.impl.Hacker.model import Hacker
from src.impl.HackerGroup.model import HackerGroup
from src.impl.Meal.model import HackerMeal, Meal
from src.impl.Operations.model import (
    CoinMovement,
    EventMentor,
    EventOperations,
    OperationAudit,
    Presentation,
    ScanRecord,
)
from src.impl.Operations.schema import EventConfig
from src.impl.User.model import User
from src.impl.Voucher.model import Voucher
from src.utils.UserType import UserType


def organizer(token):
    return token.check([UserType.LLEIDAHACKER])


def require_organizer(token):
    from src.utils.access import require_management

    require_management(token)


def state(event_id, lock=False):
    query = db.session.query(Event).filter_by(id=event_id)
    event = (query.with_for_update() if lock else query).first()
    if not event:
        raise HTTPException(404, "Event not found")
    if lock and event.archived:
        raise HTTPException(409, "Event is archived")
    row = db.session.get(EventOperations, event_id)
    if row is None:
        # Lock the parent before creating a one-to-one configuration.
        if not lock:
            db.session.query(Event).filter_by(id=event_id).with_for_update().one()
            row = db.session.get(EventOperations, event_id, populate_existing=True)
        if row is None:
            row = EventOperations(
                event_id=event_id,
                version=0,
                config=EventConfig(title=event.name).model_dump(mode="json"),
            )
            db.session.add(row)
            db.session.flush()
    return event, row


def audit(
    event_id,
    token,
    action,
    details,
    user_id=None,
    outcome="success",
    operation_id=None,
    device="",
    result=None,
):
    row = OperationAudit(
        event_id=event_id,
        actor_id=token.user_id or None,
        user_id=user_id,
        action=action,
        outcome=outcome,
        operation_id=operation_id or str(uuid4()),
        device=device,
        details=details,
        result=result or {},
    )
    db.session.add(row)
    db.session.flush()
    return row


def balance(event_id, user_id):
    return (
        db.session.query(func.coalesce(func.sum(CoinMovement.amount), 0))
        .filter_by(event_id=event_id, user_id=user_id)
        .scalar()
    )


def movement(event_id, user_id, amount, reason, log, reversal_of=None):
    before = balance(event_id, user_id)
    if before + amount < 0:
        raise HTTPException(409, "Insufficient LleidaCoins")
    row = CoinMovement(
        event_id=event_id,
        user_id=user_id,
        amount=amount,
        balance_before=before,
        balance_after=before + amount,
        reason=reason,
        audit_id=log.id,
        reversal_of=reversal_of,
    )
    db.session.add(row)
    db.session.flush()
    return row


def resolve_user(code, event_id, badge_only=False):
    voucher = db.session.query(Voucher).filter_by(code=code).first()
    if voucher:
        if voucher.revoked or voucher.event_id != event_id or not voucher.hacker_id:
            raise HTTPException(404, "Badge is unassigned or belongs to another event")
        user = db.session.get(User, voucher.hacker_id)
    else:
        if badge_only:
            raise HTTPException(
                422, "Scan the physical badge; tickets cannot be used here"
            )
        user = db.session.query(Hacker).filter_by(code=code).first()
    if not user:
        raise HTTPException(404, "Participant code not found")
    return user


def perform(event_id, body, token):
    event, row = state(event_id, lock=True)
    operation_id = str(body.operation_id)
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    previous = (
        db.session.query(OperationAudit)
        .filter_by(event_id=event_id, operation_id=operation_id)
        .first()
    )
    if previous:
        if (
            previous.actor_id != (token.user_id or None)
            or previous.details.get("fingerprint") != fingerprint
        ):
            raise HTTPException(
                409, "Operation identifier already used for a different request"
            )
        result = dict(previous.result)
        audit(
            event_id,
            token,
            "operation.replay",
            {"original_operation_id": operation_id},
            outcome="replayed",
        )
        db.session.commit()
        return result
    details = {
        "fingerprint": fingerprint,
        "target": body.target,
        "round": body.round,
        "reason": body.reason,
        "code_fingerprint": hashlib.sha256(body.code.encode()).hexdigest(),
    }
    user = None
    try:
        with db.session.begin_nested():
            if not organizer(token):
                raise HTTPException(
                    403,
                    "Nice try, farmer. This tractor does not mint LleidaCoins."
                    if body.kind in {"award", "redeem", "reverse", "void_scan"}
                    else "Organizer permission required",
                )
            if body.kind in {"award", "reverse", "void_scan"}:
                from src.utils.access import require_superadmin

                require_superadmin(token)
            user = resolve_user(
                body.code,
                event_id,
                badge_only=body.kind in {"meal", "activity", "redeem", "judging_start"},
            )
            is_mentor = user.access_role == "mentor" or user.type == "mentor"
            if is_mentor:
                mentor = db.session.get(EventMentor, (event_id, user.id))
                if not mentor or not mentor.active or user.is_deleted:
                    raise HTTPException(403, "Mentor is not active for this event")
                if body.kind not in {"meal", "void_scan"}:
                    raise HTTPException(403, "Mentor badges can only be used for meals")
            if not is_mentor and user not in event.accepted_hackers:
                raise HTTPException(403, "Participant is not accepted for this event")
            config = deepcopy(row.config)
            if (
                not is_mentor
                and body.kind != "checkin"
                and user not in event.participants
            ):
                raise HTTPException(409, "Participant must check in first")
            log = audit(
                event_id,
                token,
                body.kind,
                details,
                user.id,
                operation_id=operation_id,
                device=body.device,
            )
            result = {
                "ok": True,
                "participant": user.name,
                "user_id": user.id,
                "operation_id": operation_id,
            }
            if body.kind == "judging_start":
                from src.impl.Operations.judging import start_presentation

                result.update(
                    start_presentation(event_id, user.id, body.target, config, log)
                )
            elif body.kind in {"meal", "activity", "checkin"}:
                if body.kind == "meal":
                    meal = (
                        db.session.query(Meal)
                        .filter_by(
                            event_id=event_id,
                            id=int(body.target) if body.target.isdigit() else -1,
                        )
                        .first()
                    )
                    if not meal:
                        raise HTTPException(404, "Meal not found for this event")
                    current = config.get("meal_rounds", {}).get(
                        body.target, {"round": 1, "open": True}
                    )
                    if not current["open"]:
                        raise HTTPException(409, "Meal round is closed")
                    if current["round"] != body.round:
                        raise HTTPException(
                            409, "Meal round changed; refresh before scanning again"
                        )
                    legacy = db.session.get(HackerMeal, (user.id, meal.id))
                elif body.kind == "activity":
                    activity = next(
                        (
                            a
                            for a in config.get("activities", [])
                            if a["id"] == body.target
                        ),
                        None,
                    )
                    if not activity:
                        raise HTTPException(404, "Activity not found")
                else:
                    if user in event.participants:
                        raise HTTPException(409, "Participant already checked in")
                round_number = body.round if body.kind == "meal" else 1
                target = body.target if body.kind != "checkin" else "entry"
                existing = (
                    db.session.query(ScanRecord)
                    .filter_by(
                        event_id=event_id,
                        user_id=user.id,
                        kind=body.kind,
                        target=target,
                        round=round_number,
                        voided=False,
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(409, "Already registered in this round")
                db.session.add(
                    ScanRecord(
                        event_id=event_id,
                        user_id=user.id,
                        kind=body.kind,
                        target=target,
                        round=round_number,
                        audit_id=log.id,
                    )
                )
                if body.kind == "meal" and not legacy and not is_mentor:
                    db.session.add(HackerMeal(user_id=user.id, meal_id=meal.id))
                if body.kind == "checkin":
                    event.participants.append(user)
                if body.kind == "activity" and activity.get("points", 0):
                    movement(
                        event_id,
                        user.id,
                        activity["points"],
                        f"Activity: {activity['title']}",
                        log,
                    )
                    result["points"] = activity["points"]
            elif body.kind == "void_scan":
                original = (
                    db.session.query(ScanRecord)
                    .filter_by(
                        id=int(body.target) if body.target.isdigit() else -1,
                        event_id=event_id,
                        user_id=user.id,
                        kind="meal",
                        voided=False,
                    )
                    .first()
                )
                if not original:
                    raise HTTPException(404, "Active meal delivery not found")
                if len(body.reason.strip()) < 3:
                    raise HTTPException(422, "Correction reason required")
                original.voided = True
                log.details = {
                    **details,
                    "original_scan_id": original.id,
                    "original_audit_id": original.audit_id,
                }
                db.session.flush()
                remaining = (
                    db.session.query(ScanRecord)
                    .filter_by(
                        event_id=event_id,
                        user_id=user.id,
                        kind="meal",
                        target=original.target,
                        voided=False,
                    )
                    .count()
                )
                if not remaining:
                    legacy_meal = db.session.get(
                        HackerMeal, (user.id, int(original.target))
                    )
                    if legacy_meal:
                        db.session.delete(legacy_meal)
            elif body.kind == "award":
                if body.amount < 1 or len(body.reason.strip()) < 3:
                    raise HTTPException(422, "Positive amount and reason required")
                movement(event_id, user.id, body.amount, body.reason, log)
            elif body.kind == "redeem":
                prize = next(
                    (p for p in config.get("prizes", []) if p["id"] == body.target),
                    None,
                )
                if not prize:
                    raise HTTPException(404, "Prize not found")
                if prize["stock"] < 1:
                    raise HTTPException(409, "Prize out of stock")
                movement(
                    event_id, user.id, -prize["cost"], f"Prize: {prize['title']}", log
                )
                prize["stock"] -= 1
                row.config = config
            elif body.kind == "reverse":
                original = (
                    db.session.query(CoinMovement)
                    .filter_by(
                        id=int(body.target) if body.target.isdigit() else -1,
                        event_id=event_id,
                        user_id=user.id,
                    )
                    .first()
                )
                if not original or original.reversal_of:
                    raise HTTPException(404, "Original movement not found")
                if len(body.reason.strip()) < 3:
                    raise HTTPException(422, "Correction reason required")
                if (
                    db.session.query(CoinMovement)
                    .filter_by(reversal_of=original.id)
                    .first()
                ):
                    raise HTTPException(409, "Movement already reversed")
                movement(
                    event_id, user.id, -original.amount, body.reason, log, original.id
                )
                original_log = db.session.get(OperationAudit, original.audit_id)
                if original_log.action == "redeem":
                    prize = next(
                        (
                            p
                            for p in config.get("prizes", [])
                            if p["id"] == original_log.details.get("target")
                        ),
                        None,
                    )
                    if prize:
                        prize["stock"] += 1
                        row.config = config
            result["balance"] = balance(event_id, user.id)
            log.result = result
            row.version += 1
            db.session.flush()
        db.session.commit()
        return result
    except HTTPException as exc:
        # A rejected attempt survives the savepoint rollback, without a partial award.
        result = {
            "ok": False,
            "error": exc.detail,
            "detail": exc.detail,
            "status": exc.status_code,
            "operation_id": operation_id,
        }
        audit(
            event_id,
            token,
            body.kind,
            details,
            user.id if user else None,
            "rejected",
            operation_id,
            body.device,
            result,
        )
        db.session.commit()
        return result


def leaderboard(event_id):
    """Rank public aliases by current event balance, including ledger corrections."""
    total = func.sum(CoinMovement.amount).label("balance")
    rows = (
        db.session.query(Hacker.nickname, total)
        .join(CoinMovement, CoinMovement.user_id == Hacker.id)
        .filter(
            CoinMovement.event_id == event_id,
            Hacker.is_deleted.is_(False),
            Hacker.banned.is_(False),
            Hacker.access_role != "mentor",
        )
        .group_by(Hacker.id, Hacker.nickname)
        .order_by(total.desc(), Hacker.nickname.asc(), Hacker.id.asc())
        .limit(50)
        .all()
    )
    result = []
    previous = None
    rank = 0
    for position, row in enumerate(rows, start=1):
        if row.balance != previous:
            rank = position
        result.append(
            {
                "rank": rank,
                "nickname": row.nickname or "Hacker",
                "balance": int(row.balance),
            }
        )
        previous = row.balance
    return result


# Explicit projection: newly added management fields are private by default.
PUBLIC_CONFIG_FIELDS = {
    "title",
    "deadline",
    "judging_start",
    "judging_end",
    "phase",
    "slack_url",
    "stream_url",
    "wifi_name",
    "wifi_instructions",
    "wifi_guide_url",
    "map_url",
    "map_notes",
    "activities",
    "faqs",
    "prizes",
    "rooms",
    "slot_minutes",
    "travel_minutes",
    "game_enabled",
    "challenges_released",
    "challenge_votes_open",
    "alerts",
}


def challenges_released(config):
    return config.get("challenges_released") is True


def visible_challenges(config):
    source = "challenges" if challenges_released(config) else "decoy_challenges"
    return [
        {
            key: deepcopy(challenge[key])
            for key in ("id", "title", "description", "resources", "published")
            if key in challenge
        }
        for challenge in config.get(source, [])
        if challenge.get("published") is True
    ]


def effective_phase(config, now=None):
    """Derive the public phase without changing the organiser's configuration."""
    phase = config.get("phase", "preparation")
    if phase != "hacking" or not config.get("deadline"):
        return phase
    try:
        deadline = datetime.fromisoformat(config["deadline"])
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return phase
    return "judging" if deadline <= (now or datetime.now(UTC)) else phase


def snapshot(event_id, private=False):
    _event, row = state(event_id)
    data = (
        deepcopy(row.config)
        if private
        else {
            key: deepcopy(value)
            for key, value in row.config.items()
            if key in PUBLIC_CONFIG_FIELDS
        }
    )
    data.setdefault("alerts", [])
    data["challenges_released"] = challenges_released(row.config)
    data.setdefault("challenge_votes_open", False)
    now = datetime.now(UTC)
    data["alerts"] = [
        a
        for a in data["alerts"]
        if datetime.fromisoformat(a["expires_at"]) > now
        and (private or a.get("live", True))
    ]
    if not private:
        data["phase"] = effective_phase(row.config, now)
        data["challenges"] = visible_challenges(row.config)
        if not data["challenges_released"]:
            data["rooms"] = []
            data["challenge_votes_open"] = False
        data["activities"] = [
            a for a in data.get("activities", []) if a.get("published")
        ]
        data.pop("meal_rounds", None)
    data["event_id"] = event_id
    data["version"] = row.version
    data["server_time"] = now.isoformat()
    data["leaderboard"] = leaderboard(event_id)
    data["presentations"] = []
    if private or (data.get("phase") == "judging" and data["challenges_released"]):
        for p in (
            db.session.query(Presentation)
            .filter_by(event_id=event_id)
            .order_by(
                Presentation.room,
                case(
                    (Presentation.state == "presenting", 0),
                    (Presentation.state == "called", 1),
                    else_=2,
                ),
                Presentation.position,
                Presentation.id,
            )
        ):
            group = db.session.get(HackerGroup, p.group_id)
            data["presentations"].append({**p.to_dict(), "team": group.name})
    if private:
        data["meals"] = [
            m.to_dict() for m in db.session.query(Meal).filter_by(event_id=event_id)
        ]
        data["teams"] = [
            {"id": g.id, "name": g.name, "code": g.code}
            for g in db.session.query(HackerGroup).filter_by(event_id=event_id)
        ]
        data["meal_counts"] = [
            {
                "meal_id": m.id,
                "unique_participants": db.session.query(HackerMeal)
                .filter_by(meal_id=m.id)
                .count(),
                "rounds": [
                    {
                        "round": n,
                        "count": db.session.query(ScanRecord)
                        .filter_by(
                            event_id=event_id,
                            kind="meal",
                            target=str(m.id),
                            round=n,
                            voided=False,
                        )
                        .count(),
                    }
                    for n in range(
                        1,
                        data.get("meal_rounds", {}).get(str(m.id), {"round": 1})[
                            "round"
                        ]
                        + 1,
                    )
                ],
            }
            for m in db.session.query(Meal).filter_by(event_id=event_id)
        ]
    db.session.commit()
    return data


def schedule(event_id, token):
    require_organizer(token)
    _, row = state(event_id, True)
    config = row.config
    if not config.get("judging_start") or not config.get("judging_end"):
        raise HTTPException(422, "Judging start and end required")
    start = datetime.fromisoformat(config["judging_start"])
    end = datetime.fromisoformat(config["judging_end"])
    if effective_phase(config) == "judging":
        start = max(start, datetime.now(UTC))
    duration = timedelta(minutes=config.get("slot_minutes", 10))
    travel = timedelta(minutes=config.get("travel_minutes", 5))
    presentations = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id)
        .order_by(Presentation.id)
        .all()
    )
    from src.impl.Operations.scheduler import plan_schedule

    if start >= end:
        raise HTTPException(422, "Judging end must be after its start")
    try:
        plan = plan_schedule(presentations, start, end, duration, travel)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if plan is None:
        raise HTTPException(
            409, "Not enough time; extend judging hours or reduce slot length"
        )
    for p in presentations:
        if not p.pinned and p.state in {"waiting", "postponed"}:
            p.scheduled_at = plan[p.id]
            p.version += 1
    for room in {p.room for p in presentations}:
        for index, p in enumerate(
            sorted(
                [p for p in presentations if p.room == room],
                key=lambda x: x.scheduled_at or start,
            )
        ):
            if p.position != index:
                p.position = index
                p.version += 1
    row.version += 1
    audit(event_id, token, "judging.schedule", {"count": len(presentations)})
    db.session.commit()
    return snapshot(event_id, True)
