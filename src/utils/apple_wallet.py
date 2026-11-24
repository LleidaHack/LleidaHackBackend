"""Build signed event passes. The barcode is the existing user code, never a voucher."""

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image

# Palette and artwork from MailBackend PR #40, commit e836924.
WALLET_ART = Path(__file__).resolve().parents[2] / "static/images/wallet/hackeps-2026"


def branded_images():
    """PassKit sizes in points, with 1x/2x/3x images for Retina devices."""
    files = {}
    for scale in (1, 2, 3):
        suffix = "" if scale == 1 else f"@{scale}x"
        # Keep the logo readable without adding fields over the illustrated strip.
        strip = Image.new("RGBA", (375 * scale, 98 * scale), "#97cef2")
        for name, box, position in (
            ("cloud-left.png", (102, 62), (12, 32)),
            ("hackeps-logo.png", (78, 83), (148, 8)),
            ("cloud-right.png", (100, 45), (263, 18)),
        ):
            with Image.open(WALLET_ART / name) as source:
                artwork = source.convert("RGBA")
                artwork.thumbnail(
                    (box[0] * scale, box[1] * scale), Image.Resampling.LANCZOS
                )
                strip.alpha_composite(
                    artwork, (position[0] * scale, position[1] * scale)
                )
        # Orange border mirrors the email's orange masthead and footer.
        strip.paste("#ff7430", (0, 0, strip.width, 3 * scale))
        with Image.open(WALLET_ART / "hackeps-logo.png") as source:
            icon = source.convert("RGBA")
            icon.thumbnail((29 * scale, 29 * scale), Image.Resampling.LANCZOS)
            icon_canvas = Image.new("RGBA", (29 * scale, 29 * scale), "#97cef2")
            icon_canvas.alpha_composite(
                icon,
                (
                    (icon_canvas.width - icon.width) // 2,
                    (icon_canvas.height - icon.height) // 2,
                ),
            )
        with Image.open(WALLET_ART.parents[1] / "logo_lleidahack_blanc.png") as source:
            logo = source.convert("RGBA")
            logo.thumbnail((130 * scale, 32 * scale), Image.Resampling.LANCZOS)
        for name, picture in (("strip", strip), ("icon", icon_canvas), ("logo", logo)):
            buffer = io.BytesIO()
            picture.save(buffer, format="PNG")
            files[f"{name}{suffix}.png"] = buffer.getvalue()
    return files


def participant_role(user):
    """Display trusted account roles; this does not grant ticket eligibility."""
    role = getattr(user, "access_role", None) or getattr(user, "type", None)
    labels = {
        "hacker": "Hacker",
        "mentor": "Mentor",
        "guest": "Convidat",
        "lleidahacker": "Staff",
        "lleida_hacker": "Staff",
        "admin": "Staff",
        "superadmin": "Staff",
    }
    if role not in labels:
        raise ValueError("Unsupported Wallet participant role")
    return labels[role]


def wallet_enabled(settings):
    return bool(
        settings.apple_wallet_p12_path
        and settings.apple_wallet_password_file
        and settings.apple_wallet_wwdr_path
        and settings.apple_wallet_team_id
        and settings.apple_wallet_pass_type_id
    )


def wallet_url(settings, event_id, code):
    if not wallet_enabled(settings):
        return None
    return f"{settings.back_url.rstrip('/')}/v1/event/{event_id}/ticket/{code}/apple.pkpass"


def build_pass(settings, event, hacker):
    password = Path(settings.apple_wallet_password_file).read_bytes().rstrip(b"\r\n")
    key, certificate, _ = pkcs12.load_key_and_certificates(
        Path(settings.apple_wallet_p12_path).read_bytes(), password
    )
    if key is None or certificate is None:
        raise ValueError("Wallet certificate must include its private key")
    subject = certificate.subject
    if (
        subject.get_attributes_for_oid(NameOID.USER_ID)[0].value
        != settings.apple_wallet_pass_type_id
        or subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)[0].value
        != settings.apple_wallet_team_id
    ):
        raise ValueError("Wallet certificate identity does not match configuration")
    now = datetime.now(UTC)
    if not certificate.not_valid_before_utc <= now < certificate.not_valid_after_utc:
        raise ValueError("Wallet certificate is not currently valid")
    raw_wwdr = Path(settings.apple_wallet_wwdr_path).read_bytes()
    wwdr = (
        x509.load_pem_x509_certificate(raw_wwdr)
        if raw_wwdr.startswith(b"-----BEGIN")
        else x509.load_der_x509_certificate(raw_wwdr)
    )
    certificate.verify_directly_issued_by(wwdr)
    barcode = {
        "format": "PKBarcodeFormatQR",
        "message": hacker.code,
        "messageEncoding": "iso-8859-1",
    }
    payload = {
        "formatVersion": 1,
        "passTypeIdentifier": settings.apple_wallet_pass_type_id,
        "teamIdentifier": settings.apple_wallet_team_id,
        "serialNumber": f"event-{event.id}-hacker-{hacker.id}",
        "organizationName": "LleidaHack",
        "description": f"Entrada {event.name}",
        "foregroundColor": "rgb(247, 245, 239)",
        "backgroundColor": "rgb(46, 46, 46)",
        "labelColor": "rgb(255, 180, 140)",
        "barcodes": [barcode],
        "barcode": barcode,
        "eventTicket": {
            "headerFields": [
                {"key": "event", "label": "ESDEVENIMENT", "value": event.name}
            ],
            "secondaryFields": [
                {"key": "participant", "label": "PARTICIPANT", "value": hacker.name},
                {
                    "key": "role",
                    "label": "ROL",
                    "value": participant_role(hacker),
                    "textAlignment": "PKTextAlignmentRight",
                },
            ],
            "auxiliaryFields": [
                {
                    "key": "date",
                    "label": "DATA",
                    "value": event.start_date.strftime("%d/%m/%Y"),
                },
                {"key": "location", "label": "LLOC", "value": event.location or ""},
            ],
            "backFields": [
                {
                    "key": "checkin",
                    "label": "Check-in",
                    "value": "Mostra aquest QR a l'entrada per vincular-lo amb el teu badge físic.",
                }
            ],
        },
    }
    files = {"pass.json": json.dumps(payload, ensure_ascii=False).encode()}
    files.update(branded_images())
    # PassKit mandates SHA-1 for the manifest; the detached signature uses SHA-256.
    manifest = json.dumps(
        {name: hashlib.sha1(data).hexdigest() for name, data in files.items()}
    ).encode()
    files["manifest.json"] = manifest
    files["signature"] = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(manifest)
        .add_signer(certificate, key, hashes.SHA256())
        .add_certificate(wwdr)
        .sign(
            serialization.Encoding.DER,
            [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary],
        )
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return output.getvalue()
