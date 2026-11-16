import json
from types import SimpleNamespace
from urllib.error import HTTPError

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.utils import google_wallet as wallet


@pytest.mark.parametrize(
    "role,label", [("hacker", "Hacker"), ("mentor", "Mentor"), ("admin", "Staff")]
)
def test_save_link_is_signed_short_and_reuses_original_qr(
    tmp_path, monkeypatch, role, label
):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    secret = tmp_path / "credentials.json"
    secret.write_text(
        json.dumps(
            {
                "type": "service_account",
                "client_email": "wallet@example.test",
                "private_key": key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                ).decode(),
            }
        )
    )
    settings = SimpleNamespace(
        google_wallet_enabled=True,
        google_wallet_issuer_id="12345",
        google_wallet_credentials_path=str(secret),
        front_url="https://hackeps.dev",
    )
    stored = {}
    calls = []

    def request(url, method="GET", data=None, token=None, form=False):
        calls.append((method, url, data))
        if url == wallet.TOKEN_URL:
            claims = jwt.decode(
                data["assertion"],
                key.public_key(),
                algorithms=["RS256"],
                audience=wallet.TOKEN_URL,
            )
            assert claims["scope"].endswith("wallet_object.issuer")
            return {"access_token": "test-access-token"}
        if method == "GET":
            if url not in stored:
                raise HTTPError(url, 404, "not found", {}, None)
            return stored[url]
        target = url + "/" + data["id"] if method == "POST" else url
        stored[target] = data
        return data

    monkeypatch.setattr(wallet, "_request", request)
    user = SimpleNamespace(code="original-private-qr", name="Laia", type=role)
    event = SimpleNamespace(id=5, name="HackEPS 2026")
    link = wallet.build_save_url(settings, event, user)
    encoded = link.rsplit("/", 1)[1]
    assert len(encoded) < 1800
    claims = jwt.decode(
        encoded, key.public_key(), algorithms=["RS256"], audience="google"
    )
    object_id = claims["payload"]["eventTicketObjects"][0]["id"]
    obj = stored[wallet.API + "/eventTicketObject/" + object_id]
    assert obj["barcode"]["value"] == user.code
    assert obj["textModulesData"][0]["body"] == label
    assert user.code not in object_id
    wallet.build_save_url(settings, event, user)
    assert (
        len([c for c in calls if c[0] == "POST" and c[1].startswith(wallet.API)]) == 2
    )
    user.name = "Updated"
    wallet.build_save_url(settings, event, user)
    assert (
        stored[wallet.API + "/eventTicketObject/" + object_id]["ticketHolderName"]
        == "Updated"
    )


def test_concurrent_creation_conflict_reuses_resource(monkeypatch):
    calls = iter(
        [
            HTTPError("url", 404, "missing", {}, None),
            HTTPError("url", 409, "exists", {}, None),
            {"id": "123.test"},
        ]
    )

    def request(*args, **kwargs):
        response = next(calls)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(wallet, "_request", request)
    assert (
        wallet._ensure("eventTicketObject", {"id": "123.test"}, "token")["id"]
        == "123.test"
    )


def test_google_wallet_is_hidden_until_explicitly_enabled():
    assert wallet.google_wallet_url(SimpleNamespace(), 5, "code") is None
