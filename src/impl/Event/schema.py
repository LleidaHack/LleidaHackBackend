# from __future__ import annotations
from datetime import datetime
from typing import Optional
from src.utils.uploads import Curriculum

from pydantic import Field, field_validator

from src.utils.Base.BaseSchema import BaseSchema
from src.impl.Hacker.schema import HackerGetAll
from src.impl.HackerGroup.schema import HackerGroupGet


class ScheduleEntry(BaseSchema):
    title: str
    description: str = ""
    starts_at: Optional[str] = None

    @field_validator("starts_at")
    @classmethod
    def validate_start(cls, value):
        if value is not None:
            datetime.fromisoformat(value)
        return value


class EventCreate(BaseSchema):
    schedule: list[ScheduleEntry] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    archived: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    image: Optional[str] = None
    # is_image_url: Optional[bool] = None

    # start_time: Time = Column(Time, default=func.now())

    @field_validator("max_participants")
    @classmethod
    def max_participants_validation(cls, v):
        if v < 0:
            raise ValueError("must be a valid number")
        return v

    @field_validator("max_group_size")
    @classmethod
    def max_group_size_validation(cls, v):
        if v <= 0:
            raise ValueError("must be a valid number")
        return v

    @field_validator("max_sponsors")
    @classmethod
    def max_sponsors_validation(cls, v):
        if v < 0:
            raise ValueError("must be a valid number")
        return v


class EventGet(BaseSchema):
    schedule: list[ScheduleEntry] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    id: int
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    archived: bool
    is_open: bool
    price: int
    max_participants: int
    max_group_size: int
    max_sponsors: int
    image: Optional[str] = None
    # is_image_url: Optional[bool] = None


class EventGetAll(EventGet):
    pass


class EventUpdate(BaseSchema):
    schedule: Optional[list[ScheduleEntry]] = None
    activities: Optional[list[str]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    archived: Optional[bool] = None
    price: Optional[int] = None
    max_participants: Optional[int] = None
    max_sponsors: Optional[int] = None
    image: Optional[str] = None
    # is_image_url: Optional[bool] = None
    is_open: Optional[bool] = None
    max_group_size: Optional[int] = None

    # start_time: Time = Column(Time, default=func.now())


class HackerEventRegistration(BaseSchema):
    shirt_size: str
    food_restrictions: str
    cv: Optional[Curriculum] = None
    description: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: str
    study_center: str
    location: str
    how_did_you_meet_us: str
    wants_credit: bool
    update_user: bool

    @field_validator("shirt_size")
    @classmethod
    def shirt_size_validation(cls, v):
        if v not in ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]:
            raise ValueError("must be a valid shirt size")
        return v


class HackerEventRegistrationUpdate(BaseSchema):
    shirt_size: Optional[str] = None
    food_restrictions: Optional[str] = None
    cv: Optional[Curriculum] = None
    description: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: Optional[str] = None
    study_center: Optional[str] = None
    location: Optional[str] = None
    how_did_you_meet_us: Optional[str] = None
    wants_credit: Optional[bool] = False

    update_user: bool = False

    @field_validator("shirt_size")
    @classmethod
    def shirt_size_validation(cls, value):
        if value not in ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]:
            raise ValueError("must be a valid shirt size")
        return value


class EventGroupsGet(BaseSchema):
    success: bool
    groups: list[HackerGroupGet]


class EventHackersGet(BaseSchema):
    size: int
    hackers: list[HackerGetAll]


class RegistrationConfirmationGet(BaseSchema):
    event_id: int
    user_id: int
    confirmed_assistance: bool


class HackerEventRegistrationGet(BaseSchema):
    # Read-only view of a hacker's registration for one event. All optional and
    # without the shirt-size validator so organizers can always read whatever was
    # stored (CV, experience description, links) when reviewing acceptances.
    user_id: int
    event_id: int
    shirt_size: Optional[str] = None
    food_restrictions: Optional[str] = None
    cv: Optional[str] = None
    description: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    studies: Optional[str] = None
    study_center: Optional[str] = None
    location: Optional[str] = None
    how_did_you_meet_us: Optional[str] = None
    wants_credit: Optional[bool] = None
    confirmed_assistance: Optional[bool] = None


class EventSponsorUpdate(BaseSchema):
    tier: int
    display_order: int = 0

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, value):
        if value not in [0, 1, 2, 3]:
            raise ValueError("Unknown sponsor tier")
        return value


class EventTicketGet(BaseSchema):
    event_id: int
    event_name: Optional[str] = None
    hacker_id: int
    registered: bool
    accepted: bool
    confirmed: bool
    has_ticket: bool
    code: Optional[str] = None
    qr_url: Optional[str] = None
    ticket_sent_at: Optional[datetime] = None
    checked_in: bool
    voucher_code: Optional[str] = None


class EventTicketsStatus(BaseSchema):
    eligible: int
    sent: int
    pending: int
    running: bool
    progress: dict
