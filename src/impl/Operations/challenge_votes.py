"""Preliminary team choices, independent from submissions and judging turns."""

from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException
from fastapi_sqlalchemy import db
from pydantic import BaseModel, Field

from src.impl.HackerGroup.model import HackerGroup, HackerGroupUser
from src.impl.Operations import service as ops
from src.impl.Operations.model import ChallengeVote
from src.utils.JWTBearer import JWTBearer
from src.utils.Token import BaseToken

router = APIRouter(tags=["Event Operations"])


class ChallengeControls(BaseModel):
    version: int = Field(ge=0)
    challenges_released: bool
    challenge_votes_open: bool
    reason: str = Field(min_length=3, max_length=500)


class TeamChoice(BaseModel):
    challenge: str = Field(min_length=1, max_length=80)
    version: int = Field(ge=0)


def require_member(event_id, group_id, token, lock=False):
    query = db.session.query(HackerGroup).filter_by(id=group_id, event_id=event_id)
    group = (query.with_for_update() if lock else query).first()
    if not group:
        raise HTTPException(404, "Team not found")
    member = (
        db.session.query(HackerGroupUser)
        .filter_by(group_id=group_id, hacker_id=token.user_id)
        .first()
    )
    if not member:
        raise HTTPException(403, "Only current team members can choose its challenge")
    return group


def choices(config):
    if not config.get("challenges_released", True):
        return []
    return [
        {"id": c["id"], "title": c["title"], "description": c.get("description", "")}
        for c in config.get("challenges", [])
        if c.get("published") and c["id"] != "mlh"
    ]


def team_snapshot(event_id, group_id, state):
    vote = (
        db.session.query(ChallengeVote)
        .filter_by(event_id=event_id, group_id=group_id)
        .first()
    )
    return {
        "open": bool(
            state.config.get("challenge_votes_open", False)
            and state.config.get("challenges_released", True)
        ),
        "published": state.config.get("challenges_released", True),
        "challenges": choices(state.config),
        "choice": vote.challenge if vote else None,
        "version": vote.version if vote else 0,
    }


@router.put("/{event_id}/challenge-controls")
def controls(
    event_id: int, body: ChallengeControls, token: BaseToken = Depends(JWTBearer())
):
    ops.require_organizer(token)
    _, state = ops.state(event_id, True)
    if state.version != body.version:
        raise HTTPException(409, "Configuration changed; refresh before saving")
    config = deepcopy(state.config)
    before = {
        k: config.get(k, k == "challenges_released")
        for k in ("challenges_released", "challenge_votes_open")
    }
    config.update(
        challenges_released=body.challenges_released,
        challenge_votes_open=body.challenge_votes_open,
    )
    if body.challenge_votes_open and not choices(config):
        raise HTTPException(
            422, "Publish at least one challenge before opening choices"
        )
    state.config = config
    state.version += 1
    ops.audit(
        event_id,
        token,
        "challenge.controls",
        {"before": before, "after": body.model_dump(), "reason": body.reason},
    )
    db.session.commit()
    return ops.snapshot(event_id, True)


@router.get("/{event_id}/teams/{group_id}/challenge-vote")
def current_choice(
    event_id: int, group_id: int, token: BaseToken = Depends(JWTBearer())
):
    require_member(event_id, group_id, token)
    _, state = ops.state(event_id)
    result = team_snapshot(event_id, group_id, state)
    db.session.commit()
    return result


@router.put("/{event_id}/teams/{group_id}/challenge-vote")
def choose(
    event_id: int,
    group_id: int,
    body: TeamChoice,
    token: BaseToken = Depends(JWTBearer()),
):
    _, state = ops.state(event_id, True)
    require_member(event_id, group_id, token, lock=True)
    if not state.config.get("challenge_votes_open", False):
        raise HTTPException(409, "Challenge choices are closed")
    if body.challenge not in {c["id"] for c in choices(state.config)}:
        raise HTTPException(422, "Select a published challenge")
    vote = (
        db.session.query(ChallengeVote)
        .filter_by(event_id=event_id, group_id=group_id)
        .first()
    )
    if body.version != (vote.version if vote else 0):
        raise HTTPException(409, "Your team choice changed; refresh before saving")
    before = vote.challenge if vote else None
    if vote and before == body.challenge:
        return team_snapshot(event_id, group_id, state)
    if vote:
        vote.challenge = body.challenge
        vote.version += 1
    else:
        vote = ChallengeVote(
            event_id=event_id, group_id=group_id, challenge=body.challenge
        )
        db.session.add(vote)
    ops.audit(
        event_id,
        token,
        "challenge.vote",
        {"group_id": group_id, "before": before, "after": body.challenge},
    )
    db.session.flush()
    result = team_snapshot(event_id, group_id, state)
    db.session.commit()
    return result


@router.get("/{event_id}/challenge-votes")
def results(event_id: int, token: BaseToken = Depends(JWTBearer())):
    ops.require_organizer(token)
    _, state = ops.state(event_id)
    teams = list(
        db.session.query(HackerGroup)
        .filter_by(event_id=event_id)
        .order_by(HackerGroup.id)
    )
    votes = {
        v.group_id: v
        for v in db.session.query(ChallengeVote).filter_by(event_id=event_id)
    }
    rows = [
        {
            "group_id": g.id,
            "team": g.name,
            "challenge": votes[g.id].challenge if g.id in votes else None,
        }
        for g in teams
    ]
    result = {
        "total_teams": len(teams),
        "voted": sum(r["challenge"] is not None for r in rows),
        "teams": rows,
        "challenges": [
            {
                "id": c["id"],
                "title": c["title"],
                "count": sum(r["challenge"] == c["id"] for r in rows),
            }
            for c in state.config.get("challenges", [])
        ],
    }
    db.session.commit()
    return result
