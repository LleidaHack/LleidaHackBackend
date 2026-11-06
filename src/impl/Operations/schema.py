from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class Resource(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    url: HttpUrl


class Challenge(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=10000)
    resources: list[Resource] = Field(default_factory=list, max_length=30)
    published: bool = False


class Activity(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=150)
    start: datetime
    end: datetime
    location: str = Field(default="", max_length=200)
    points: int = Field(default=0, ge=0, le=10000)
    published: bool = True

    @field_validator("start", "end")
    @classmethod
    def timezone_required(cls, value):
        if not value.tzinfo:
            raise ValueError("Timezone required")
        return value


class FAQ(BaseModel):
    question: str = Field(min_length=1, max_length=300)
    answer: str = Field(min_length=1, max_length=5000)


class Prize(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=150)
    cost: int = Field(ge=1, le=1000000)
    stock: int = Field(ge=0, le=100000)


class Room(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=150)
    paused: bool = False


class EventConfig(BaseModel):
    title: str = Field(default="HackEPS", max_length=150)
    deadline: datetime | None = None
    judging_start: datetime | None = None
    judging_end: datetime | None = None
    phase: Literal["preparation", "hacking", "judging", "finished"] = "preparation"
    slack_url: HttpUrl | None = None
    stream_url: HttpUrl | None = None
    wifi_name: str = Field(default="", max_length=200)
    wifi_instructions: str = Field(default="", max_length=2000)
    wifi_guide_url: HttpUrl | None = None
    map_url: HttpUrl | None = None
    map_notes: str = Field(default="", max_length=10000)
    challenges: list[Challenge] = Field(default_factory=list, max_length=30)
    decoy_challenges: list[Challenge] = Field(default_factory=list, max_length=30)
    activities: list[Activity] = Field(default_factory=list, max_length=200)
    faqs: list[FAQ] = Field(default_factory=list, max_length=100)
    prizes: list[Prize] = Field(default_factory=list, max_length=100)
    rooms: list[Room] = Field(default_factory=list, max_length=30)
    slot_minutes: int = Field(default=10, ge=1, le=120)
    travel_minutes: int = Field(default=5, ge=0, le=60)
    game_enabled: bool = True
    challenges_released: bool = False
    challenge_votes_open: bool = False

    @field_validator("deadline", "judging_start", "judging_end")
    @classmethod
    def timezone_required(cls, value):
        if value and not value.tzinfo:
            raise ValueError("Timezone required")
        return value


class ConfigUpdate(BaseModel):
    version: int
    config: EventConfig
    reason: str = Field(min_length=3, max_length=500)


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    device: str = Field(default="", max_length=100)
    kind: Literal[
        "meal", "activity", "checkin", "award", "redeem", "reverse", "void_scan"
    ]
    code: str = Field(min_length=1, max_length=500)
    target: str = Field(default="", max_length=100)
    round: int = Field(default=1, ge=1)
    amount: int = Field(default=0, ge=0, le=1000000, strict=True)
    reason: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def server_owned_rewards(self):
        if self.kind != "award" and self.amount != 0:
            raise ValueError("Only manual awards accept a client-supplied amount")
        if self.kind != "meal" and self.round != 1:
            raise ValueError("Only meals support additional rounds")
        return self


class RoundUpdate(BaseModel):
    expected_round: int = Field(ge=1)
    action: Literal["next", "close", "open"]
    reason: str = Field(min_length=3, max_length=500)


class Alert(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    message: str = Field(min_length=1, max_length=2000)
    level: Literal["info", "warning", "danger"] = "info"
    expires_at: datetime
    push: bool = False
    live: bool = True
    discord: bool = False
    category: Literal["general", "activity", "meal"] = "general"


class Enroll(BaseModel):
    challenge: str
    mlh: bool = False
    reason: str = Field(default="Team selection", min_length=3, max_length=500)


class PresentationUpdate(BaseModel):
    version: int
    state: Literal["waiting", "called", "presenting", "done", "absent", "postponed"]
    room: str
    position: int = Field(ge=0)
    scheduled_at: datetime | None = None
    pinned: bool = False
    override: bool = False
    reason: str = Field(min_length=3, max_length=500)
