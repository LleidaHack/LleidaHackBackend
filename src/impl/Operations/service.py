"""Event-scoped operations with atomic audit, replay protection and row locking."""

import hashlib
import re
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from fastapi_sqlalchemy import db
from sqlalchemy import case, func, or_, text
from sqlalchemy.orm import aliased

from src.impl.Event.model import Event, HackerRegistration
from src.impl.Hacker.model import Hacker
from src.impl.HackerGroup.model import HackerGroup
from src.impl.Meal.model import HackerMeal, Meal
from src.impl.Operations.model import (
    ChallengeVote,
    CoinMovement,
    EventGuest,
    EventMentor,
    EventOperations,
    OperationAudit,
    Presentation,
    ScanRecord,
)
from src.impl.Operations.schema import EventConfig
from src.impl.User.model import User
from src.impl.Voucher.model import Voucher
from src.utils.event_tickets import STAFF_ROLES
from src.utils.UserType import UserType

# Scan kinds a non-hacker badge (mentor, guest, company, staff) may perform.
BADGE_HOLDER_KINDS = frozenset({"meal", "activity", "void_scan"})

_EVENT_TABLES = {"hacker_event_accepted", "hacker_event_participation"}


def in_event_table(table, event_id, user_id):
    """Membership check without loading the whole collection under the event lock."""
    assert table in _EVENT_TABLES
    return (
        db.session.execute(
            text(f"SELECT 1 FROM {table} WHERE event_id = :e AND user_id = :u LIMIT 1"),
            {"e": event_id, "u": user_id},
        ).first()
        is not None
    )


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
            if "hackeps" in event.name.casefold():
                from src.impl.Operations.ribo import ensure_room

                ensure_room(row)
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


def meal_people(event_id, meal_id):
    """Unique recipients across legacy deliveries and current scans, including mentors."""
    legacy = db.session.query(HackerMeal.user_id).filter_by(meal_id=meal_id)
    scanned = db.session.query(ScanRecord.user_id).filter_by(
        event_id=event_id, kind="meal", target=str(meal_id), voided=False
    )
    return legacy.union(scanned).count()


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


def perform(event_id, body, token, allow_ticket_meal=False):
    # Non-organizers are always rejected (and audited) without mutating state, so
    # they must not take the event lock that serializes real scans.
    event, row = state(event_id, lock=organizer(token))
    operation_id = str(body.operation_id)
    # Preserve fingerprints of scans queued before duration/guess support was
    # deployed: optional inputs that were not sent stay out of the hash.
    fingerprint = hashlib.sha256(
        body.model_dump_json(
            exclude={
                field
                for field in ("duration_ms", "guess")
                if getattr(body, field) is None
            }
        ).encode()
    ).hexdigest()
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
    if body.duration_ms is not None:
        details["duration_ms"] = body.duration_ms
    if body.guess is not None:
        details["guess"] = body.guess
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
                badge_only=body.kind in {"meal", "activity", "redeem", "judging_start"}
                # The legacy /meal/{id}/eat/{code} route keeps accepting ticket codes.
                and not (allow_ticket_meal and body.kind == "meal"),
            )
            # Mentors, guests, companies and staff are not hackers, but once a
            # physical badge is bound to them they use it for meals and activities.
            badge_holder = user.access_role == "mentor" or user.type == "mentor"
            if badge_holder:
                mentor = db.session.get(EventMentor, (event_id, user.id))
                if not mentor or not mentor.active or user.is_deleted:
                    raise HTTPException(403, "Mentor is not active for this event")
            if user.access_role == "guest":
                guest = db.session.get(EventGuest, (event_id, user.id))
                if not guest or not guest.active or user.is_deleted:
                    raise HTTPException(403, "Guest is not active for this event")
                badge_holder = True
            if user.access_role in STAFF_ROLES:
                if user.is_deleted:
                    raise HTTPException(403, "Staff member is not active")
                badge_holder = True
            if badge_holder and body.kind not in BADGE_HOLDER_KINDS:
                raise HTTPException(
                    403, "This badge can only be used for meals and activities"
                )
            if not badge_holder and not in_event_table(
                "hacker_event_accepted", event_id, user.id
            ):
                raise HTTPException(403, "Participant is not accepted for this event")
            config = deepcopy(row.config)
            if (
                not badge_holder
                and body.kind != "checkin"
                and not in_event_table("hacker_event_participation", event_id, user.id)
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
                from src.impl.Operations.judging import (
                    announce_called,
                    start_presentation,
                )

                result.update(
                    start_presentation(event_id, user.id, body.target, config, log)
                )
                announce_called(row, log.details.get("transitions", []))
            elif body.kind in {"meal", "activity", "checkin"}:
                if body.kind == "meal":
                    meal = (
                        db.session.query(Meal)
                        .filter_by(
                            event_id=event_id,
                            id=int(body.target)
                            if re.fullmatch(r"[0-9]{1,9}", body.target)
                            else -1,
                        )
                        .first()
                    )
                    if not meal:
                        raise HTTPException(404, "Meal not found for this event")
                    # Canonicalise ("07" -> "7") so round state and duplicate checks
                    # cannot be bypassed with an equivalent spelling of the meal id.
                    body = body.model_copy(update={"target": str(meal.id)})
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
                    if activity.get("timed", False) != (body.duration_ms is not None):
                        raise HTTPException(
                            422,
                            "Timed activities require a duration; other activities do not accept one",
                        )
                    if body.duration_ms is not None:
                        result["duration_ms"] = body.duration_ms
                    if activity.get("coin_guess", False) != (body.guess is not None):
                        raise HTTPException(
                            422,
                            "LleidaCoins counting activities require a guess; other activities do not accept one",
                        )
                    if body.guess is not None:
                        result["guess"] = body.guess
                else:
                    if in_event_table("hacker_event_participation", event_id, user.id):
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
                # Timed attempts and guesses may be scanned again (a new attempt,
                # or a corrected guess); everything else counts once per round.
                if existing and body.duration_ms is None and body.guess is None:
                    raise HTTPException(409, "Already registered in this round")
                if not existing:
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
                if body.kind == "meal" and not legacy and not badge_holder:
                    db.session.add(HackerMeal(user_id=user.id, meal_id=meal.id))
                if body.kind == "checkin":
                    event.participants.append(user)
                if (
                    body.kind == "activity"
                    and not existing
                    and not badge_holder  # LleidaCoins are for hackers only
                    and activity.get("points", 0)
                ):
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
                        id=int(body.target)
                        if re.fullmatch(r"[0-9]{1,9}", body.target)
                        else -1,
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
                        id=int(body.target)
                        if re.fullmatch(r"[0-9]{1,9}", body.target)
                        else -1,
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
            if body.kind == "meal":
                registration = (
                    db.session.query(HackerRegistration)
                    .filter_by(event_id=event_id, user_id=user.id)
                    .first()
                )
                result["food_restrictions"] = (
                    registration.food_restrictions
                    if registration is not None
                    else user.food_restrictions
                )
            result["balance"] = balance(event_id, user.id)
            log.result = result
            row.version += 1
            db.session.flush()
        db.session.commit()
        if body.kind == "judging_start":
            from src.impl.Operations.realtime import broadcast_alerts

            broadcast_alerts(event_id)
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


def coin_totals(query):
    """Join a CoinMovement query with its sources and build per-person totals.

    ``earned`` ignores prize redemptions (and reversals of redemptions), so
    spending LleidaCoins never lowers it; ``balance`` is what is left to spend.
    Returns the joined query and the ``(earned, spent, balance)`` columns.
    """
    # Aliases are built per call: aliasing at import time would configure the
    # mappers before every model module has been imported.
    original = aliased(CoinMovement)
    original_audit = aliased(OperationAudit)
    prize = or_(OperationAudit.action == "redeem", original_audit.action == "redeem")
    query = (
        query.join(OperationAudit, OperationAudit.id == CoinMovement.audit_id)
        .outerjoin(original, original.id == CoinMovement.reversal_of)
        .outerjoin(original_audit, original_audit.id == original.audit_id)
    )
    return query, (
        func.sum(case((prize, 0), else_=CoinMovement.amount)).label("earned"),
        (-func.sum(case((prize, CoinMovement.amount), else_=0))).label("spent"),
        func.sum(CoinMovement.amount).label("balance"),
    )


def leaderboard(event_id):
    """Rank public aliases by LleidaCoins earned in the event.

    Redeeming prizes does not lower a position; other corrections (reversed
    awards) do. The value is still exposed as ``balance`` for Live clients.
    """
    query, (earned, _spent, _balance) = coin_totals(
        db.session.query(Hacker).join(CoinMovement, CoinMovement.user_id == Hacker.id)
    )
    rows = (
        query.with_entities(Hacker.id, Hacker.nickname, earned)
        .filter(
            CoinMovement.event_id == event_id,
            Hacker.is_deleted.is_(False),
            Hacker.banned.is_(False),
            Hacker.access_role != "mentor",
        )
        .group_by(Hacker.id, Hacker.nickname)
        .order_by(earned.desc(), Hacker.nickname.asc(), Hacker.id.asc())
        .limit(50)
        .all()
    )
    result = []
    previous = None
    rank = 0
    for position, row in enumerate(rows, start=1):
        if row.earned != previous:
            rank = position
        result.append(
            {
                "rank": rank,
                "nickname": row.nickname or "Hacker",
                "balance": int(row.earned),
            }
        )
        previous = row.earned
    return result


def balances(event_id):
    """Organizer view: earned, spent on prizes and remaining LleidaCoins."""
    query, (earned, spent, balance) = coin_totals(
        db.session.query(User).join(CoinMovement, CoinMovement.user_id == User.id)
    )
    rows = (
        query.with_entities(User.id, User.name, User.nickname, earned, spent, balance)
        .filter(CoinMovement.event_id == event_id)
        .group_by(User.id, User.name, User.nickname)
        .order_by(balance.desc(), User.name.asc(), User.id.asc())
        .all()
    )
    return [
        {
            "user_id": row.id,
            "name": row.name,
            "nickname": row.nickname,
            "earned": int(row.earned),
            "spent": int(row.spent),
            "balance": int(row.balance),
        }
        for row in rows
    ]


# Explicit projection: newly added management fields are private by default.
PUBLIC_CONFIG_FIELDS = {
    "title",
    "deadline",
    "judging_start",
    "judging_end",
    "phase",
    "slack_url",
    "stream_url",
    "stream_enabled",
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
            for key in (
                "id",
                "company",
                "title",
                "description",
                "resources",
                "published",
            )
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


def visible_live_alert(alert, now):
    return (
        alert.get("live", True)
        and datetime.fromisoformat(alert["expires_at"]) > now
        and (
            not alert.get("scheduled_at")
            or datetime.fromisoformat(alert["scheduled_at"]) <= now
        )
    )


def live_alert_window(event_id):
    _, row = state(event_id)
    now = datetime.now(UTC)
    alerts = (row.config or {}).get("alerts", [])
    visible = [a for a in alerts if visible_live_alert(a, now)]
    next_start = min(
        (
            start
            for a in alerts
            if a.get("live", True)
            and a.get("scheduled_at")
            and (start := datetime.fromisoformat(a["scheduled_at"])) > now
        ),
        default=None,
    )
    return visible, next_start


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
        and (private or visible_live_alert(a, now))
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
        # One query for team names instead of one per presentation (polled publicly).
        team_names = dict(
            db.session.query(HackerGroup.id, HackerGroup.name).filter_by(
                event_id=event_id
            )
        )
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
            team = team_names.get(p.group_id)
            if team is None:
                team = db.session.get(HackerGroup, p.group_id).name
            data["presentations"].append({**p.to_dict(), "team": team})
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
                "unique_participants": meal_people(event_id, m.id),
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


def ribo_teams(event_id):
    return {
        gid
        for (gid,) in db.session.query(ChallengeVote.group_id).filter_by(
            event_id=event_id, ribo_prize=True
        )
    }


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
        plan = plan_schedule(
            presentations, start, end, duration, travel, ribo_teams(event_id)
        )
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
