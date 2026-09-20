"""Validate untrusted participant uploads and store a canonical, inert format."""
import base64
import binascii
import io
import warnings
from typing import Annotated

from PIL import Image, UnidentifiedImageError
from pydantic import AfterValidator
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

MAX_FILE_BYTES = 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
MIME_FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


def decode_upload(value, allowed):
    if len(value) > 4 * ((MAX_FILE_BYTES + 2) // 3) + 64:
        raise ValueError("File exceeds 1 MiB")
    header, separator, encoded = value.partition(",")
    if not separator or not header.startswith("data:") or not header.endswith(";base64"):
        raise ValueError("Upload a file, not a URL")
    mime = header[5:-7]
    if mime not in allowed:
        raise ValueError("Unsupported file type")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid file encoding") from exc
    if not raw or len(raw) > MAX_FILE_BYTES:
        raise ValueError("File must be non-empty and at most 1 MiB")
    return mime, raw


def encode_upload(mime, raw):
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("Processed file exceeds 1 MiB")
    return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")


def validate_image(value):
    if value in (None, ""):
        return value
    mime, raw = decode_upload(value, MIME_FORMATS)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                if image.format != MIME_FORMATS[mime]:
                    raise ValueError("Image content does not match its type")
                if image.width * image.height > MAX_IMAGE_PIXELS or getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Image dimensions or animation are not supported")
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                # Copy only decoded pixels: discard EXIF, embedded text, trailing
                # polyglot payloads and all other user-provided metadata.
                mode = "RGB" if mime == "image/jpeg" else "RGBA"
                clean = Image.new(mode, image.size)
                clean.paste(image.convert(mode))
                output = io.BytesIO()
                clean.save(output, format=MIME_FORMATS[mime])
        return encode_upload(mime, output.getvalue())
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise ValueError("Invalid or unsafe image") from exc


# Reject active content anywhere in the reachable object graph, including
# encoded PDF names and indirect references (a byte-string search is not enough).
FORBIDDEN_PDF_KEYS = {"/AA", "/OpenAction", "/JS", "/JavaScript", "/EmbeddedFiles",
                      "/EF", "/XFA", "/RichMediaContent", "/RichMediaSettings"}
FORBIDDEN_PDF_ACTIONS = {"/JavaScript", "/Launch", "/SubmitForm", "/ImportData",
                         "/GoToR", "/GoToE", "/Rendition", "/RichMediaExecute"}


def validate_cv(value):
    if value in (None, ""):
        return value
    mime, raw = decode_upload(value, {"application/pdf"})
    if not raw.startswith(b"%PDF-"):
        raise ValueError("CV must contain a PDF document")
    try:
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported")
        visited = set()
        pending = [reader.trailer]
        count = 0
        while pending:
            obj = pending.pop()
            count += 1
            if count > 50_000:
                raise ValueError("PDF is too complex")
            if isinstance(obj, IndirectObject):
                key = (obj.idnum, obj.generation)
                if key in visited:
                    continue
                visited.add(key)
                obj = obj.get_object()
            if isinstance(obj, DictionaryObject):
                if FORBIDDEN_PDF_KEYS.intersection(obj.keys()) or obj.get("/S") in FORBIDDEN_PDF_ACTIONS:
                    raise ValueError("PDF contains active content or attachments")
                if obj.get("/Type") == "/EmbeddedFile" or obj.get("/Subtype") in {"/RichMedia", "/FileAttachment"}:
                    raise ValueError("PDF contains embedded content")
                pending.extend(obj.values())
            elif isinstance(obj, ArrayObject):
                pending.extend(obj)
        if not 1 <= len(reader.pages) <= 20:
            raise ValueError("CV must contain between 1 and 20 pages")
        writer = PdfWriter()
        for page in reader.pages:
            # Retain page content, but not actions, interactive widgets, links,
            # document metadata, forms or trailing non-PDF payloads.
            writer.add_page(page, excluded_keys=["/Annots", "/AA"])
        output = io.BytesIO()
        writer.write(output)
        return encode_upload(mime, output.getvalue())
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Invalid or unsafe PDF") from exc


ProfileImage = Annotated[str, AfterValidator(validate_image)]
Curriculum = Annotated[str, AfterValidator(validate_cv)]
