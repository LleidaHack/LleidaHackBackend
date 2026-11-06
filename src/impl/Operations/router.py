import os
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from fastapi_sqlalchemy import db
from pydantic import BaseModel, HttpUrl, ValidationError

from src.impl.HackerGroup.model import HackerGroup
from src.impl.Meal.model import Meal
from src.impl.Operations import service as ops
from src.impl.Operations.access_router import RoleUpdate, assign_role
from src.impl.Operations.model import (
    CoinMovement,
    DiscordDelivery,
    OperationAudit,
    Presentation,
    PushDelivery,
    PushSubscription,
)
from src.impl.Operations.schema import (
    Alert,
    ConfigUpdate,
    Enroll,
    Operation,
    PresentationUpdate,
    RoundUpdate,
)
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(prefix="/operations", tags=["Event Operations"])


@router.get("/{event_id}/public")
def public_snapshot(event_id: int):
    return ops.snapshot(event_id)


@router.get("/{event_id}/challenges")
def public_challenges(event_id: int):
    _, row = ops.state(event_id)
    result = {"challenges": ops.visible_challenges(row.config)}
    db.session.commit()
    return result


@router.get("/{event_id}/broadcast")
def public_broadcast(event_id: int):
    ops.state(event_id)
    from src.impl.Operations.youtube import current_broadcast

    return current_broadcast()


@router.get("/{event_id}/manage")
def management_snapshot(event_id: int, token: BaseToken = Depends(JWTBearer())):
    ops.require_organizer(token)
    from src.utils.access import access_role

    return {**ops.snapshot(event_id, True), "access_role": access_role(token)}


@router.put("/{event_id}/config")
def update_config(
    event_id: int, body: ConfigUpdate, token: BaseToken = Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    if row.version != body.version:
        raise HTTPException(409, "Configuration changed; refresh before saving")
    config = body.config.model_dump(mode="json")
    for key in ("challenges", "decoy_challenges", "activities", "prizes", "rooms"):
        ids = [item["id"] for item in config[key]]
        if len(ids) != len(set(ids)):
            raise HTTPException(422, f"Duplicate {key} identifiers")
    if any(a.end <= a.start for a in body.config.activities):
        raise HTTPException(422, "Activity end must follow its start")
    used_rooms = {
        p.room for p in db.session.query(Presentation).filter_by(event_id=event_id)
    }
    if not used_rooms.issubset({r["id"] for r in config["rooms"]}):
        raise HTTPException(409, "Move presentations before removing a room")
    before = deepcopy(row.config)
    from src.utils.access import require_superadmin

    critical_changed = any(config.get(key) != before.get(key) for key in ("deadline",))
    critical_changed = critical_changed or {
        a["id"]: a.get("points", 0) for a in config["activities"]
    } != {a["id"]: a.get("points", 0) for a in before.get("activities", [])}
    critical_changed = critical_changed or {
        p["id"]: (p["cost"], p["stock"]) for p in config["prizes"]
    } != {p["id"]: (p["cost"], p["stock"]) for p in before.get("prizes", [])}
    critical_changed = critical_changed or (
        "challenges_released" in body.config.model_fields_set
        and config["challenges_released"] != ops.challenges_released(before)
    )
    if critical_changed:
        require_superadmin(token)
    for key, default in (
        ("challenges_released", False),
        ("challenge_votes_open", False),
    ):
        if key not in body.config.model_fields_set:
            config[key] = before.get(key, default)
    if "decoy_challenges" not in body.config.model_fields_set:
        config["decoy_challenges"] = before.get("decoy_challenges", [])
    if config.get("challenge_votes_open") and (
        not config.get("challenges_released")
        or not any(c["published"] and c["id"] != "mlh" for c in config["challenges"])
    ):
        raise HTTPException(
            422, "Publish at least one challenge before opening choices"
        )
    for key in ("meal_rounds", "alerts"):
        config[key] = before.get(key, {} if key == "meal_rounds" else [])
    row.config = config
    row.version += 1
    ops.audit(
        event_id,
        token,
        "config.update",
        {"reason": body.reason, "before": before, "after": config},
    )
    db.session.commit()
    return ops.snapshot(event_id, True)


@router.post("/{event_id}/scan")
def scan(event_id: int, body: dict, token: BaseToken = Depends(JWTBearer())):
    try:
        operation = Operation.model_validate(body)
    except ValidationError as exc:
        ops.state(event_id, True)
        # Keep evidence of tampering without persisting arbitrary attacker payloads.
        ops.audit(
            event_id,
            token,
            "security.invalid_scan",
            {
                "fields": [
                    ".".join(str(part) for part in error["loc"])[:100]
                    for error in exc.errors()
                ][:20],
                "reason": "Invalid scan payload; client-supplied rewards are not trusted",
            },
            outcome="rejected",
        )
        db.session.commit()
        return JSONResponse(
            {
                "ok": False,
                "error": "Nice try, farmer. This tractor does not mint LleidaCoins.",
                "code": "TRACTOR_NOT_A_MINT",
                "detail": "Nice try, farmer. This tractor does not mint LleidaCoins.",
            },
            status_code=422,
        )
    result = ops.perform(event_id, operation, token)
    return JSONResponse(result, status_code=200 if result["ok"] else result["status"])


@router.post("/{event_id}/meals/{meal_id}/round")
def meal_round(
    event_id: int,
    meal_id: int,
    body: RoundUpdate,
    token: BaseToken = Depends(JWTBearer()),
):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    if not db.session.query(Meal).filter_by(id=meal_id, event_id=event_id).first():
        raise HTTPException(404, "Meal not found")
    config = deepcopy(row.config)
    rounds = config.setdefault("meal_rounds", {})
    current = rounds.setdefault(str(meal_id), {"round": 1, "open": True})
    if current["round"] != body.expected_round:
        raise HTTPException(409, "Round changed; refresh first")
    before = dict(current)
    if body.action == "next":
        current["round"] += 1
    current["open"] = body.action != "close"
    row.config = config
    row.version += 1
    ops.audit(
        event_id,
        token,
        "meal.round",
        {"meal_id": meal_id, "before": before, "after": current, "reason": body.reason},
    )
    db.session.commit()
    return current


@router.get("/{event_id}/audit")
def operation_history(
    event_id: int,
    before: int | None = None,
    action: str | None = None,
    user_id: int | None = None,
    token: BaseToken = Depends(JWTBearer()),
):
    ops.require_organizer(token)
    query = db.session.query(OperationAudit).filter_by(event_id=event_id)
    if before:
        query = query.filter(OperationAudit.id < before)
    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    from src.impl.Operations.model import ScanRecord
    from src.impl.User.model import User

    entries = []
    for entry in query.order_by(OperationAudit.id.desc()).limit(100):
        actor = db.session.get(User, entry.actor_id) if entry.actor_id else None
        participant = db.session.get(User, entry.user_id) if entry.user_id else None
        entries.append(
            {
                **entry.to_dict(),
                "actor_name": actor.name if actor else "Service",
                "participant_name": participant.name if participant else None,
                "movements": [
                    m.to_dict()
                    for m in db.session.query(CoinMovement).filter_by(audit_id=entry.id)
                ],
                "scans": [
                    s.to_dict()
                    for s in db.session.query(ScanRecord).filter_by(audit_id=entry.id)
                ],
            }
        )
    return entries


@router.get("/{event_id}/wallet")
def wallet(event_id: int, token: BaseToken = Depends(JWTBearer())):
    if not token.available or not token.user_id:
        raise HTTPException(403, "User session required")
    return {
        "balance": ops.balance(event_id, token.user_id),
        "movements": [
            m.to_dict()
            for m in db.session.query(CoinMovement)
            .filter_by(event_id=event_id, user_id=token.user_id)
            .order_by(CoinMovement.id.desc())
            .limit(200)
        ],
    }


@router.post("/{event_id}/alerts")
def publish_alert(event_id: int, body: Alert, token: BaseToken = Depends(JWTBearer())):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    if not body.expires_at.tzinfo or body.expires_at <= datetime.now(UTC):
        raise HTTPException(422, "Future expiry with timezone required")
    if not (body.live or body.push or body.discord):
        raise HTTPException(422, "Select at least one alert destination")
    if body.push and not os.getenv("VAPID_PRIVATE_KEY"):
        raise HTTPException(503, "Web Push is not configured")
    alert = {
        **body.model_dump(mode="json"),
        "id": str(uuid4()),
        "event_id": event_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    config = deepcopy(row.config)
    config.setdefault("alerts", []).append(alert)
    row.config = config
    row.version += 1
    if body.push:
        for subscription in db.session.query(PushSubscription).filter_by(
            event_id=event_id
        ):
            db.session.add(
                PushDelivery(
                    event_id=event_id,
                    subscription_id=subscription.id,
                    alert_id=alert["id"],
                    payload=alert,
                )
            )
    if body.discord:
        db.session.add(
            DiscordDelivery(event_id=event_id, alert_id=alert["id"], payload=alert)
        )
    ops.audit(event_id, token, "alert.publish", alert)
    db.session.commit()
    from src.impl.Operations.realtime import broadcast_alerts

    broadcast_alerts(event_id)
    return alert


@router.delete("/{event_id}/alerts/{alert_id}")
def remove_alert(event_id: int, alert_id: str, token: BaseToken = Depends(JWTBearer())):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    config = deepcopy(row.config)
    config["alerts"] = [a for a in config.get("alerts", []) if a["id"] != alert_id]
    row.config = config
    row.version += 1
    db.session.query(PushDelivery).filter_by(
        event_id=event_id, alert_id=alert_id, state="pending"
    ).update({"state": "cancelled"})
    db.session.query(DiscordDelivery).filter(
        DiscordDelivery.event_id == event_id,
        DiscordDelivery.alert_id == alert_id,
        DiscordDelivery.state.in_(["pending", "leased"]),
    ).update({"state": "cancelled"})
    ops.audit(event_id, token, "alert.remove", {"alert_id": alert_id})
    db.session.commit()
    from src.impl.Operations.realtime import broadcast_alerts

    broadcast_alerts(event_id)
    return {"ok": True}


@router.post("/{event_id}/teams/{group_id}/enroll")
def enroll_team(
    event_id: int, group_id: int, body: Enroll, token: BaseToken = Depends(JWTBearer())
):
    _, row = ops.state(event_id, True)
    group = (
        db.session.query(HackerGroup).filter_by(id=group_id, event_id=event_id).first()
    )
    if not group:
        raise HTTPException(404, "Team not found")
    if not ops.organizer(token) and (
        group.leader_id != token.user_id or row.config.get("phase") != "hacking"
    ):
        raise HTTPException(
            403, "Only the team leader during hacking or an organizer can enroll"
        )
    if not ops.challenges_released(row.config):
        ops.require_organizer(token)
    challenges = {
        c["id"] for c in row.config.get("challenges", []) if c.get("published")
    }
    rooms = {r["id"] for r in row.config.get("rooms", [])}
    if (
        body.challenge not in challenges
        or body.challenge not in rooms
        or (body.mlh and "mlh" not in rooms)
    ):
        raise HTTPException(422, "Select a published challenge with a configured room")
    existing = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id, group_id=group_id)
        .all()
    )
    if any(p.state not in {"waiting", "postponed"} for p in existing):
        raise HTTPException(409, "Presentations have started; use the room controls")
    for p in existing:
        db.session.delete(p)
    db.session.flush()
    for track in [body.challenge] + (["mlh"] if body.mlh else []):
        db.session.add(
            Presentation(event_id=event_id, group_id=group_id, room=track, track=track)
        )
    row.version += 1
    ops.audit(
        event_id, token, "judging.enroll", {"group_id": group_id, **body.model_dump()}
    )
    db.session.commit()
    return {"ok": True}


@router.post("/{event_id}/schedule")
def generate_schedule(event_id: int, token: BaseToken = Depends(JWTBearer())):
    return ops.schedule(event_id, token)


@router.patch("/{event_id}/presentations/{presentation_id}")
def change_presentation(
    event_id: int,
    presentation_id: int,
    body: PresentationUpdate,
    token: BaseToken = Depends(JWTBearer()),
):
    ops.require_organizer(token)
    _, row = ops.state(event_id, True)
    p = (
        db.session.query(Presentation)
        .filter_by(event_id=event_id, id=presentation_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Presentation not found")
    if p.version != body.version:
        raise HTTPException(409, "Presentation changed; refresh first")
    room = next((r for r in row.config.get("rooms", []) if r["id"] == body.room), None)
    if not room:
        raise HTTPException(422, "Unknown room")
    if body.scheduled_at and not body.scheduled_at.tzinfo:
        raise HTTPException(422, "Timezone required")
    if body.override:
        from src.utils.access import require_superadmin

        require_superadmin(token)
    if not body.override:
        if room.get("paused") and body.state in {"called", "presenting"}:
            raise HTTPException(409, "Room is paused")
        others = (
            db.session.query(Presentation)
            .filter(Presentation.event_id == event_id, Presentation.id != p.id)
            .all()
        )
        for other in others:
            if (
                body.state in {"called", "presenting"}
                and other.state in {"called", "presenting"}
                and (other.room == body.room or other.group_id == p.group_id)
            ):
                raise HTTPException(
                    409, "Room or team already has an active presentation"
                )
            if (
                body.scheduled_at
                and other.scheduled_at
                and (other.room == body.room or other.group_id == p.group_id)
            ):
                gap = timedelta(
                    minutes=row.config.get("slot_minutes", 10)
                    + (
                        row.config.get("travel_minutes", 5)
                        if other.group_id == p.group_id
                        else 0
                    )
                )
                if abs(body.scheduled_at - other.scheduled_at) < gap:
                    raise HTTPException(
                        409, "Schedule conflict; adjust time or explicitly override"
                    )
    before = p.to_dict()
    before["scheduled_at"] = p.scheduled_at.isoformat() if p.scheduled_at else None
    for key in ("state", "room", "position", "scheduled_at"):
        setattr(p, key, getattr(body, key))
    p.pinned = int(body.pinned)
    p.version += 1
    row.version += 1
    ops.audit(
        event_id,
        token,
        "judging.update",
        {"before": before, "after": body.model_dump(mode="json")},
    )
    db.session.commit()
    return {"ok": True}


class SubscriptionInput(BaseModel):
    endpoint: HttpUrl
    keys: dict[str, str]


@router.get("/{event_id}/push-key")
def push_key(event_id: int):
    return {"public_key": os.getenv("VAPID_PUBLIC_KEY", "")}


@router.post("/{event_id}/subscribe")
def subscribe(event_id: int, body: SubscriptionInput):
    from urllib.parse import urlparse

    endpoint = str(body.endpoint)
    host = urlparse(endpoint).hostname or ""
    # Do not turn the push worker into an arbitrary HTTP request proxy.
    allowed = (
        host == "fcm.googleapis.com"
        or host == "updates.push.services.mozilla.com"
        or host.endswith((".push.apple.com", ".notify.windows.com"))
        or host == "web.push.apple.com"
    )
    if (
        not allowed
        or not endpoint.startswith("https://")
        or not all(body.keys.get(k) for k in ("p256dh", "auth"))
    ):
        raise HTTPException(422, "Unsupported push endpoint or missing keys")
    ops.state(event_id, True)
    subscription = (
        db.session.query(PushSubscription).filter_by(endpoint=endpoint).first()
    )
    if subscription and subscription.event_id != event_id:
        raise HTTPException(409, "Subscription already belongs to another event")
    if not subscription:
        db.session.add(
            PushSubscription(
                event_id=event_id,
                endpoint=endpoint,
                subscription=body.model_dump(mode="json"),
            )
        )
    db.session.commit()
    return {"ok": True}


@router.get("/{event_id}/scanner")
def scanner_configuration(event_id: int, token: BaseToken = Depends(JWTBearer())):
    if not ops.organizer(token):
        raise HTTPException(403, "Organizer permission required")
    from src.utils.access import access_role

    data = ops.snapshot(event_id, True)
    return {
        "event_id": event_id,
        "title": data["title"],
        "meals": data["meals"],
        "meal_rounds": data.get("meal_rounds", {}),
        "activities": [a for a in data["activities"] if a["published"]],
        "prizes": data["prizes"],
        "access_role": access_role(token),
    }


@router.get("/{event_id}/staff")
def staff_roles(event_id: int, token: BaseToken = Depends(JWTBearer())):
    from src.impl.User.model import User
    from src.utils.access import require_superadmin

    require_superadmin(token)
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.access_role}
        for u in db.session.query(User).filter_by(is_deleted=False).order_by(User.id)
    ]


@router.patch("/{event_id}/staff/{user_id}")
def update_staff_role(
    event_id: int,
    user_id: int,
    body: RoleUpdate,
    token: BaseToken = Depends(JWTBearer()),
):
    ops.state(event_id, True)
    return assign_role(user_id, body, token, event_id)


@router.websocket("/{event_id}/ws")
async def live_alerts(websocket: WebSocket, event_id: int):
    from src.impl.Operations.realtime import alert_socket

    await alert_socket(websocket, event_id)


from src.impl.Operations.devpost import router as devpost_router

router.include_router(devpost_router)

from src.impl.Operations.challenge_votes import router as challenge_vote_router

router.include_router(challenge_vote_router)
