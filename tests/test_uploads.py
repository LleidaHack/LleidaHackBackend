import base64
import io
from datetime import UTC, datetime, timedelta

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from src.utils.uploads import MAX_FILE_BYTES, validate_cv, validate_image


def data_uri(mime, raw):
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def png():
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "orange").save(output, format="PNG")
    return output.getvalue()


def pdf(writer=None):
    writer = writer or PdfWriter()
    writer.add_blank_page(width=200, height=200)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize(
    "value",
    [
        "https://example.test/photo.png",
        data_uri("image/svg+xml", b'<svg onload="alert(1)"/>'),
        data_uri("image/png", b"<script>alert(1)</script>"),
        "data:image/png;base64,@@@",
    ],
)
def test_rejects_urls_scripts_and_fake_images(value):
    with pytest.raises(ValueError):
        validate_image(value)


@pytest.mark.parametrize(
    "format,mime",
    [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")],
)
def test_images_are_decoded_and_reencoded_without_trailing_payload(format, mime):
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "orange").save(output, format=format)
    clean = validate_image(
        data_uri(mime, output.getvalue() + b"<script>bad()</script>")
    )
    raw = base64.b64decode(clean.split(",")[1])
    assert b"<script>" not in raw
    with Image.open(io.BytesIO(raw)) as image:
        assert image.size == (8, 8)
        assert image.format == format


def test_image_type_and_size_limits(monkeypatch):
    with pytest.raises(ValueError):
        validate_image(data_uri("image/jpeg", png()))
    with pytest.raises(ValueError):
        validate_image(data_uri("image/png", b"a" * (MAX_FILE_BYTES + 1)))
    monkeypatch.setattr("src.utils.uploads.MAX_IMAGE_PIXELS", 63)
    with pytest.raises(ValueError):
        validate_image(data_uri("image/png", png()))


@pytest.mark.parametrize("payload", ["script", "attachment", "encrypted"])
def test_active_or_encrypted_pdf_is_rejected(payload):
    writer = PdfWriter()
    if payload == "script":
        writer.add_js("app.alert('test')")
    elif payload == "attachment":
        writer.add_attachment("test.js", b"alert(1)")
    else:
        writer.encrypt("test-password")
    with pytest.raises(ValueError):
        validate_cv(data_uri("application/pdf", pdf(writer)))


def test_pdf_is_rebuilt_without_metadata_or_appended_payload():
    writer = PdfWriter()
    writer.add_metadata({"/Subject": "untrusted-metadata"})
    cleaned = validate_cv(
        data_uri("application/pdf", pdf(writer) + b"<script>bad()</script>")
    )
    raw = base64.b64decode(cleaned.split(",")[1])
    assert b"untrusted-metadata" not in raw
    assert b"<script>" not in raw
    assert len(PdfReader(io.BytesIO(raw)).pages) == 1


def test_invalid_pdf_and_oversized_pdf_are_rejected():
    for raw in [
        b"%PDF-1.7 not actually a document",
        b"<html>script</html>",
        b"x" * (MAX_FILE_BYTES + 1),
    ]:
        with pytest.raises(ValueError):
            validate_cv(data_uri("application/pdf", raw))


def test_upload_validation_cannot_be_bypassed_using_api(
    client, create_user, create_event
):
    user = create_user()
    event = create_event([user])
    assert (
        client.put(
            f"/v1/hacker/{user.id}",
            headers=user.headers,
            json={"image": "https://example.test/image.png"},
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/v1/hacker/{user.id}",
            headers=user.headers,
            json={"image": data_uri("image/png", png())},
        ).status_code
        == 200
    )
    bad_cv = data_uri("application/pdf", b"<script>bad()</script>")
    assert (
        client.put(
            f"/v1/event/{event}/update-register/{user.id}",
            headers=user.headers,
            json={"cv": bad_cv},
        ).status_code
        == 422
    )
    response = client.put(
        f"/v1/hacker/{user.id}",
        headers=user.headers,
        json={"cv": data_uri("application/pdf", pdf())},
    )
    assert response.status_code == 200, response.text


def test_creation_timestamp_is_computed_for_each_new_user(monkeypatch):
    from src.impl.User import model

    column = model.User.__table__.c.created_at
    assert column.default.is_callable
    first = column.default.arg(None)
    future = datetime.now(UTC) + timedelta(days=2)

    class Clock:
        @staticmethod
        def now(tz):
            return future

    monkeypatch.setattr(model, "datetime", Clock)
    assert column.default.arg(None) - first > timedelta(days=1)


def test_profile_creation_timestamp_contains_time_and_timezone(client, create_user):
    user = create_user()
    response = client.get(f"/v1/hacker/{user.id}", headers=user.headers)
    assert response.status_code == 200
    created = datetime.fromisoformat(response.json()["created_at"])
    assert created.tzinfo is not None
    assert abs((datetime.now(UTC) - created).total_seconds()) < 10


def test_valid_file_under_one_mib_survives_base64_request_overhead(client, create_user):
    import os

    user = create_user()
    output = io.BytesIO()
    Image.frombytes("RGB", (576, 480), os.urandom(576 * 480 * 3)).save(
        output, format="PNG"
    )
    raw = output.getvalue()
    image = data_uri("image/png", raw)
    assert len(raw) < MAX_FILE_BYTES < len(image)
    response = client.put(
        f"/v1/hacker/{user.id}", headers=user.headers, json={"image": image}
    )
    assert response.status_code == 200, response.text
