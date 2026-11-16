"""Issue Google event tickets with the existing check-in QR and short save JWTs."""

import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt

from src.utils.apple_wallet import participant_role
from src.utils.ticket_links import public_ticket_url

API = "https://walletobjects.googleapis.com/walletobjects/v1"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def google_wallet_enabled(settings):
    return bool(
        getattr(settings, "google_wallet_enabled", False)
        and getattr(settings, "google_wallet_issuer_id", "")
        and getattr(settings, "google_wallet_credentials_path", "")
    )


def google_wallet_url(settings, event_id, code):
    if not google_wallet_enabled(settings):
        return None
    return public_ticket_url(settings, event_id, code) + "/google-wallet"


def _request(url, method="GET", data=None, token=None, form=False):
    body = (
        (urlencode(data).encode() if form else json.dumps(data).encode())
        if data is not None
        else None
    )
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
        if form
        else "application/json"
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    # All URLs are fixed Google endpoints plus internally generated identifiers.
    with urlopen(
        Request(url, data=body, headers=headers, method=method), timeout=15
    ) as response:
        return json.load(response)


def _ensure(resource, payload, token):
    url = f"{API}/{resource}/{payload['id']}"
    try:
        return _request(url, token=token)
    except HTTPError as exc:
        if exc.code != 404:
            raise
    try:
        return _request(f"{API}/{resource}", "POST", payload, token)
    except HTTPError as exc:
        if exc.code != 409:
            raise
        # Another request may have created the same event/object concurrently.
        return _request(url, token=token)


def build_save_url(settings, event, user):
    credentials = json.loads(Path(settings.google_wallet_credentials_path).read_text())
    issuer = settings.google_wallet_issuer_id
    if not issuer.isdigit() or credentials.get("type") != "service_account":
        raise ValueError("Invalid Google Wallet configuration")
    now = int(time.time())
    assertion = jwt.encode(
        {
            "iss": credentials["client_email"],
            "aud": TOKEN_URL,
            "scope": "https://www.googleapis.com/auth/wallet_object.issuer",
            "iat": now,
            "exp": now + 3600,
        },
        credentials["private_key"],
        algorithm="RS256",
    )
    token = _request(
        TOKEN_URL,
        "POST",
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        },
        form=True,
    )["access_token"]
    class_id = f"{issuer}.hackeps_event_{event.id}"
    # Do not expose the bearer code as a visible ticket number or an object ID.
    object_id = f"{issuer}.ticket_{event.id}_{hashlib.sha256(user.code.encode()).hexdigest()[:32]}"
    origin = public_ticket_url(settings, event.id, user.code).split("/entrada/")[0]

    def image(path, label):
        return {
            "sourceUri": {"uri": origin + "/entrada/imatges/" + path},
            "contentDescription": {"defaultValue": {"language": "ca", "value": label}},
        }

    _ensure(
        "eventTicketClass",
        {
            "id": class_id,
            "issuerName": "LleidaHack",
            "reviewStatus": "UNDER_REVIEW",
            "eventName": {"defaultValue": {"language": "ca", "value": event.name}},
            "logo": image("wallet/google-logo.png", "LleidaHack"),
            "heroImage": image("wallet/google-hero.png", "HackEPS"),
            "hexBackgroundColor": "#2e2e2e",
        },
        token,
    )
    payload = {
        "id": object_id,
        "classId": class_id,
        "state": "ACTIVE",
        "ticketHolderName": user.name or "",
        "barcode": {
            "type": "QR_CODE",
            "value": user.code,
            "alternateText": "Entrada personal",
        },
        "textModulesData": [
            {"id": "role", "header": "Rol", "body": participant_role(user)}
        ],
    }
    current = _ensure("eventTicketObject", payload, token)
    if any(current.get(k) != v for k, v in payload.items()):
        _request(f"{API}/eventTicketObject/{object_id}", "PATCH", payload, token)
    signed = jwt.encode(
        {
            "iss": credentials["client_email"],
            "aud": "google",
            "typ": "savetowallet",
            "iat": now,
            "payload": {"eventTicketObjects": [{"id": object_id}]},
        },
        credentials["private_key"],
        algorithm="RS256",
    )
    return "https://pay.google.com/gp/v/save/" + signed
