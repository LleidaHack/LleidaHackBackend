"""Print-ready accreditation badges: the marketing design with a unique QR each.

1. Gestió → event → Check-in: generate the vouchers and export the CSV.
2. Check the position with a single proof page, the square outlined in red:

     uv run python scripts/badge_print.py front.png vouchers_event_7.csv \\
         --width-mm 90 --x 126 --y 949 --size 269 --limit 1 --outline -o prova.pdf

3. Generate the print file (one front, and its back if given, per voucher):

     uv run python scripts/badge_print.py front.png vouchers_event_7.csv \\
         --back back.png --width-mm 90 --x 126 --y 949 --size 269 -o hackers.pdf

Designs can be PDFs (positions in millimetres from the top-left corner of the
trim box, i.e. the final cut size) or PNG/JPEG artwork (positions in pixels of
the image; --width-mm sets the printed width and --bleed-mm extends the edges
outwards for the cut). The QR is drawn as vector shapes, encodes exactly the
voucher code the HackEPS scanner expects and has the code printed under it in
case a camera cannot read it. Each design is embedded once and reused by every
page, so the file stays small. Use --skip/--limit to take consecutive slices of
the same CSV for differently coloured badges.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import segno
from PIL import Image
from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    RectangleObject,
)

MM = 72 / 25.4
CODE_PATTERN = re.compile(r"V[A-HJ-NP-Z2-9]{8}")
# The scanner needs a light margin of a few modules around the code.
QUIET_ZONE_MODULES = 2
# Courier glyphs are 0.6 em wide, so the code can be centred exactly.
COURIER_WIDTH = 0.6
MIN_SIZE_MM = 20
RASTER_SUFFIXES = {".png", ".jpg", ".jpeg"}


def read_codes(path: Path, only_unassigned: bool = False) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "code" not in rows[0]:
        raise SystemExit(f"{path}: expected the Gestió voucher CSV (column 'code')")
    codes = [
        row["code"].strip()
        for row in rows
        if not (only_unassigned and (row.get("hacker_id") or "").strip())
    ]
    invalid = [code for code in codes if not CODE_PATTERN.fullmatch(code)]
    if invalid:
        raise SystemExit(f"Invalid voucher codes: {', '.join(invalid[:5])}")
    duplicated = {code for code in codes if codes.count(code) > 1}
    if duplicated:
        raise SystemExit(f"Duplicated voucher codes: {', '.join(sorted(duplicated))}")
    return codes


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def overlay_stream(
    code: str,
    left: float,
    top: float,
    size: float,
    *,
    print_code: bool = True,
    outline: bool = False,
    quiet_zone: int = QUIET_ZONE_MODULES,
    fill: bool = True,
) -> bytes:
    """PDF drawing commands for the QR (and code) inside the white square.

    `left`/`top` are the square's top-left corner in PDF points.
    """
    matrix = segno.make(code, error="h", micro=False).matrix
    modules = len(matrix) + 2 * quiet_zone
    text_size = size * 0.075 if print_code else 0
    text_gap = text_size * 0.6 if print_code else 0
    qr_side = size - text_size - text_gap
    module = qr_side / modules
    qr_left = left + (size - qr_side) / 2
    qr_top = top
    bottom = top - size

    ops = ["q"]
    if fill:
        ops += ["1 g", f"{_fmt(left)} {_fmt(bottom)} {_fmt(size)} {_fmt(size)} re f"]
    ops.append("0 g")
    for row_index, row in enumerate(matrix):
        y = qr_top - (row_index + quiet_zone + 1) * module
        col = 0
        while col < len(row):
            if not row[col]:
                col += 1
                continue
            start = col
            while col < len(row) and row[col]:
                col += 1
            x = qr_left + (start + quiet_zone) * module
            # A hairline overlap avoids white seams between modules in some RIPs.
            ops.append(
                f"{_fmt(x)} {_fmt(y)} {_fmt((col - start) * module + 0.02)} "
                f"{_fmt(module + 0.02)} re"
            )
    ops.append("f")
    if print_code:
        width = len(code) * COURIER_WIDTH * text_size
        x = left + (size - width) / 2
        y = bottom + text_size * 0.35
        ops += [
            "BT",
            f"/FQR {_fmt(text_size)} Tf",
            f"{_fmt(x)} {_fmt(y)} Td",
            f"({code}) Tj",
            "ET",
        ]
    if outline:
        ops += [
            "1 0 0 RG",
            "0.5 w",
            f"{_fmt(left)} {_fmt(bottom)} {_fmt(size)} {_fmt(size)} re S",
        ]
    ops.append("Q")
    return "\n".join(ops).encode()


@dataclass
class Design:
    page: PageObject
    # PDF points per design unit: millimetres for PDFs, pixels for artwork.
    unit: float
    raster: bool


def _bleed_canvas(image: Image.Image, bleed: int) -> Image.Image:
    """Extend the outermost pixels outwards so the cut never shows a white edge."""
    if bleed <= 0:
        return image
    width, height = image.size
    canvas = Image.new("RGB", (width + 2 * bleed, height + 2 * bleed))
    canvas.paste(image, (bleed, bleed))
    canvas.paste(image.crop((0, 0, width, 1)).resize((width, bleed)), (bleed, 0))
    canvas.paste(
        image.crop((0, height - 1, width, height)).resize((width, bleed)),
        (bleed, bleed + height),
    )
    canvas.paste(
        canvas.crop((bleed, 0, bleed + 1, height + 2 * bleed)).resize(
            (bleed, height + 2 * bleed)
        ),
        (0, 0),
    )
    canvas.paste(
        canvas.crop((bleed + width - 1, 0, bleed + width, height + 2 * bleed)).resize(
            (bleed, height + 2 * bleed)
        ),
        (bleed + width, 0),
    )
    return canvas


def _raster_pdf(path: Path, width_mm: float, bleed_mm: float) -> tuple[bytes, float]:
    image = Image.open(path)
    image = image.convert("RGB")
    width, height = image.size
    scale = width_mm * MM / width
    bleed = round(bleed_mm * MM / scale)
    canvas = _bleed_canvas(image, bleed)
    total_w, total_h = canvas.size[0] * scale, canvas.size[1] * scale

    art = DecodedStreamObject()
    art.set_data(canvas.tobytes())
    art.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(canvas.size[0]),
            NameObject("/Height"): NumberObject(canvas.size[1]),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    writer = PdfWriter()
    page = writer.add_blank_page(width=total_w, height=total_h)
    page[NameObject("/TrimBox")] = RectangleObject(
        [
            bleed * scale,
            bleed * scale,
            (bleed + width) * scale,
            (bleed + height) * scale,
        ]
    )
    page[NameObject("/BleedBox")] = RectangleObject([0, 0, total_w, total_h])
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject(
                {NameObject("/Art"): writer._add_object(art.flate_encode())}
            )
        }
    )
    content = DecodedStreamObject()
    content.set_data(f"q {_fmt(total_w)} 0 0 {_fmt(total_h)} 0 0 cm /Art Do Q".encode())
    page[NameObject("/Contents")] = writer._add_object(content)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue(), scale


def load_design(
    path: Path,
    *,
    page_number: int = 1,
    width_mm: float | None = None,
    bleed_mm: float = 3,
) -> Design:
    if path.suffix.lower() in RASTER_SUFFIXES:
        if not width_mm:
            raise SystemExit("Artwork images need --width-mm (printed badge width)")
        data, scale = _raster_pdf(path, width_mm, bleed_mm)
        return Design(PdfReader(io.BytesIO(data)).pages[0], scale, raster=True)
    reader = PdfReader(path)
    if not 1 <= page_number <= len(reader.pages):
        raise SystemExit(f"{path} has {len(reader.pages)} page(s)")
    page = reader.pages[page_number - 1]
    if page.rotation:
        raise SystemExit("Rotated design pages are not supported; export it upright")
    return Design(page, MM, raster=False)


def _design_form(writer: PdfWriter, template: PageObject):
    """The design page as a Form XObject, embedded once and drawn on every badge."""
    contents = template.get_contents()
    form = DecodedStreamObject()
    # ContentStream is a dict subtype: an empty dictionary is falsy.
    form.set_data(contents.get_data() if contents is not None else b"")
    form.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): ArrayObject(template.mediabox),
            NameObject("/Resources"): (
                template["/Resources"].get_object().clone(writer)
                if "/Resources" in template
                else DictionaryObject()
            ),
        }
    )
    return writer._add_object(form.flate_encode())


def _font(writer: PdfWriter):
    return writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Courier-Bold"),
            }
        )
    )


def _copy_boxes(page: PageObject, template: PageObject) -> None:
    for box in ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox"):
        if box in template:
            page[NameObject(box)] = ArrayObject(template[box])


def build(
    front: Design,
    codes: list[str],
    output: Path,
    *,
    x: float,
    y: float,
    size: float,
    back: Design | None = None,
    print_code: bool = True,
    outline: bool = False,
    quiet_zone: int = QUIET_ZONE_MODULES,
    fill: bool = True,
) -> int:
    """Write one page per code (followed by the back, if any).

    `x`, `y` and `size` are in the front design's units (see `Design.unit`).
    """
    template = front.page
    trim = template.trimbox
    left = float(trim.left) + x * front.unit
    top = float(trim.top) - y * front.unit
    size = size * front.unit
    if size < MIN_SIZE_MM * MM - 1e-6:
        raise SystemExit(
            f"The QR square would print {size / MM:.1f} mm wide; "
            f"at least {MIN_SIZE_MM} mm is needed to scan reliably"
        )
    if (
        left < float(trim.left)
        or top > float(trim.top)
        or left + size > float(trim.right)
        or top - size < float(trim.bottom)
    ):
        raise SystemExit("The QR square falls outside the badge (check --x/--y/--size)")

    writer = PdfWriter()
    font = DictionaryObject({NameObject("/FQR"): _font(writer)})
    front_resources = writer._add_object(
        DictionaryObject(
            {
                NameObject("/XObject"): DictionaryObject(
                    {NameObject("/Design"): _design_form(writer, template)}
                ),
                NameObject("/Font"): font,
            }
        )
    )
    back_page = None
    if back is not None:
        back_content = DecodedStreamObject()
        back_content.set_data(b"q /Design Do Q")
        back_page = (
            writer._add_object(
                DictionaryObject(
                    {
                        NameObject("/XObject"): DictionaryObject(
                            {NameObject("/Design"): _design_form(writer, back.page)}
                        )
                    }
                )
            ),
            writer._add_object(back_content),
        )
    for code in codes:
        page = writer.add_blank_page(
            width=float(template.mediabox.width),
            height=float(template.mediabox.height),
        )
        _copy_boxes(page, template)
        page[NameObject("/Resources")] = front_resources
        content = DecodedStreamObject()
        content.set_data(
            b"q /Design Do Q\n"
            + overlay_stream(
                code,
                left,
                top,
                size,
                print_code=print_code,
                outline=outline,
                quiet_zone=quiet_zone,
                fill=fill,
            )
        )
        page[NameObject("/Contents")] = writer._add_object(content.flate_encode())
        if back_page is not None:
            reverse = writer.add_blank_page(
                width=float(back.page.mediabox.width),
                height=float(back.page.mediabox.height),
            )
            _copy_boxes(reverse, back.page)
            reverse[NameObject("/Resources")] = back_page[0]
            reverse[NameObject("/Contents")] = back_page[1]
    with output.open("wb") as handle:
        writer.write(handle)
    return len(codes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("design", type=Path, help="badge front (PDF, PNG or JPEG)")
    parser.add_argument("csv", type=Path, help="voucher CSV exported from Gestió")
    parser.add_argument("-o", "--output", type=Path, default=Path("acreditacions.pdf"))
    parser.add_argument("--back", type=Path, help="badge back, printed after each")
    parser.add_argument(
        "--x", type=float, required=True, help="square left (mm, or px for images)"
    )
    parser.add_argument(
        "--y", type=float, required=True, help="square top (mm, or px for images)"
    )
    parser.add_argument(
        "--size", type=float, required=True, help="square side (mm, or px for images)"
    )
    parser.add_argument("--width-mm", type=float, help="printed width of images")
    parser.add_argument(
        "--bleed-mm", type=float, default=3, help="bleed added to images (default 3)"
    )
    parser.add_argument("--page", type=int, default=1, help="PDF design page to use")
    parser.add_argument("--skip", type=int, default=0, help="skip the first N codes")
    parser.add_argument("--limit", type=int, help="only N vouchers (after --skip)")
    parser.add_argument(
        "--only-unassigned",
        action="store_true",
        help="skip vouchers already bound to a participant",
    )
    parser.add_argument(
        "--no-code", action="store_true", help="do not print the code under the QR"
    )
    parser.add_argument(
        "--outline", action="store_true", help="outline the square in red (proofs)"
    )
    parser.add_argument(
        "--quiet-zone",
        type=int,
        default=QUIET_ZONE_MODULES,
        choices=range(5),
        metavar="0-4",
        help=f"white margin around the QR, in modules (default {QUIET_ZONE_MODULES})",
    )
    parser.add_argument(
        "--no-fill",
        action="store_true",
        help="do not paint the square white (keeps rounded artwork corners)",
    )
    args = parser.parse_args(argv)

    codes = read_codes(args.csv, args.only_unassigned)[args.skip :]
    if args.limit is not None:
        if len(codes) < args.limit:
            raise SystemExit(f"Only {len(codes)} vouchers left; generate more first")
        codes = codes[: args.limit]
    if not codes:
        raise SystemExit("No vouchers to print")
    options = {"width_mm": args.width_mm, "bleed_mm": args.bleed_mm}
    front = load_design(args.design, page_number=args.page, **options)
    back = load_design(args.back, **options) if args.back else None
    count = build(
        front,
        codes,
        args.output,
        x=args.x,
        y=args.y,
        size=args.size,
        back=back,
        print_code=not args.no_code,
        outline=args.outline,
        quiet_zone=args.quiet_zone,
        fill=not args.no_fill,
    )
    print(
        f"{count} badges ({codes[0]} … {codes[-1]}) written to {args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
