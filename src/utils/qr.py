import io

import segno

from src.configuration.Settings import settings


def qr_png(data: str, scale: int = 8) -> bytes:
    """Render `data` as a PNG QR code (error level H so a logo/print damage still scans)."""
    buffer = io.BytesIO()
    segno.make(data, error="h").save(buffer, kind="png", scale=scale, border=2)
    return buffer.getvalue()


def ticket_qr_url(event_id: int, code: str) -> str:
    """Public URL of a hacker's ticket QR, embeddable in mails (Gmail blocks data: URIs)."""
    return f"{settings.back_url.rstrip('/')}/v1/event/{event_id}/ticket/{code}/qr.png"
