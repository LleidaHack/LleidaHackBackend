"""Public ticket links use the event website, including for non-account holders."""

from urllib.parse import quote, urlsplit


def public_ticket_url(settings, event_id: int, code: str) -> str:
    front = urlsplit(settings.front_url)
    origin = f"{front.scheme}://{front.netloc}"
    return f"{origin}/entrada/{event_id}/{quote(code, safe='')}"
