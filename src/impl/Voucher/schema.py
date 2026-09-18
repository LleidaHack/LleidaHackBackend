from datetime import datetime
from typing import List, Optional

from pydantic import Field

from src.utils.Base.BaseSchema import BaseSchema


class VoucherGenerate(BaseSchema):
    count: int = Field(ge=1, le=2000)


class VoucherHacker(BaseSchema):
    id: int
    name: str
    nickname: Optional[str] = None
    email: Optional[str] = None


class VoucherGet(BaseSchema):
    id: int
    event_id: int
    code: str
    hacker_id: Optional[int] = None
    hacker: Optional[VoucherHacker] = None
    created_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None


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
    hacker_shirt_size: Optional[str] = None
    food_restrictions: Optional[str] = None
    message: str = ""


class VoucherGenerateResult(BaseSchema):
    success: bool = True
    created: int
    vouchers: List[VoucherGet]
