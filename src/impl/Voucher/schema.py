from datetime import datetime

from pydantic import Field

from src.utils.Base.BaseSchema import BaseSchema


class VoucherGenerate(BaseSchema):
    count: int = Field(ge=1, le=2000)


class VoucherHacker(BaseSchema):
    id: int
    name: str
    nickname: str | None = None
    email: str | None = None


class VoucherGet(BaseSchema):
    id: int
    event_id: int
    code: str
    hacker_id: int | None = None
    hacker: VoucherHacker | None = None
    created_at: datetime | None = None
    assigned_at: datetime | None = None


class VoucherSummary(BaseSchema):
    total: int
    assigned: int
    unassigned: int


class VoucherAssignResult(BaseSchema):
    success: bool = True
    event_id: int
    voucher_code: str
    hacker_id: int
    hacker_name: str
    hacker_shirt_size: str | None = None
    food_restrictions: str | None = None
    message: str = ""


class VoucherGenerateResult(BaseSchema):
    success: bool = True
    created: int
    vouchers: list[VoucherGet]
