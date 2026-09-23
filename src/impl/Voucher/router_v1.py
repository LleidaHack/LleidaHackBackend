from fastapi import APIRouter, Depends, Response

from src.impl.Voucher.schema import (
    VoucherAssignResult,
    VoucherGenerate,
    VoucherGenerateResult,
    VoucherGet,
    VoucherSummary,
)
from src.impl.Voucher.service import VoucherService
from src.utils.JWTBearer import JWTBearer
from src.utils.qr import qr_png
from src.utils.Token import BaseToken

router = APIRouter(
    prefix="/event/{event_id}/vouchers",
    tags=["Voucher"],
)

voucher_service = VoucherService()


@router.post("/generate", response_model=VoucherGenerateResult)
def generate(
    event_id: int, payload: VoucherGenerate, token: BaseToken = Depends(JWTBearer())
):
    """Create `count` blank vouchers (physical badges) for the event."""
    vouchers = voucher_service.generate(event_id, payload.count, token)
    return {"success": True, "created": len(vouchers), "vouchers": vouchers}


@router.get("/", response_model=list[VoucherGet])
def get_all(
    event_id: int,
    assigned: bool | None = None,
    token: BaseToken = Depends(JWTBearer()),
):
    return voucher_service.get_all(event_id, token, assigned)


@router.get("/summary", response_model=VoucherSummary)
def get_summary(event_id: int, token: BaseToken = Depends(JWTBearer())):
    return voucher_service.get_summary(event_id, token)


@router.get("/export.csv")
def export_csv(event_id: int, token: BaseToken = Depends(JWTBearer())):
    """CSV with every voucher code, ready for the print shop."""
    content = voucher_service.export_csv(event_id, token)
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="vouchers_event_{event_id}.csv"'
        },
    )


@router.get("/{voucher_code}", response_model=VoucherGet)
def get_voucher(
    event_id: int, voucher_code: str, token: BaseToken = Depends(JWTBearer())
):
    return voucher_service.get_voucher(event_id, voucher_code, token)


@router.get("/{voucher_code}/qr.png")
def get_voucher_qr(
    event_id: int, voucher_code: str, token: BaseToken = Depends(JWTBearer())
):
    voucher = voucher_service.get_voucher(event_id, voucher_code, token)
    return Response(content=qr_png(voucher.code), media_type="image/png")


@router.put("/{voucher_code}/assign/{hacker_code}", response_model=VoucherAssignResult)
def assign(
    event_id: int,
    voucher_code: str,
    hacker_code: str,
    token: BaseToken = Depends(JWTBearer()),
):
    """Check-in: scan the hacker's ticket, then the physical voucher, and bind them."""
    return voucher_service.assign(event_id, voucher_code, hacker_code, token)


@router.delete("/{voucher_code}/assign", response_model=VoucherGet)
def unassign(event_id: int, voucher_code: str, token: BaseToken = Depends(JWTBearer())):
    """Release a voucher (lost or damaged badge) so another one can be assigned."""
    return voucher_service.unassign(event_id, voucher_code, token)
