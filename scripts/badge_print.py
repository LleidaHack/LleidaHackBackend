"""Print-ready accreditation badges: the marketing design with a unique QR each.

1. Gestió → event → Check-in: generate the vouchers and export the CSV.
2. Run (positions in millimetres from the top-left corner of the trim box,
   i.e. the final cut size; the bleed is outside it):

     uv run python scripts/badge_print.py disseny.pdf vouchers_event_7.csv \\
         --x 27.5 --y 70 --size 30 -o acreditacions.pdf

   Check the position first with a single proof page and the square outlined:

     uv run python scripts/badge_print.py disseny.pdf vouchers_event_7.csv \\
         --x 27.5 --y 70 --size 30 --limit 1 --outline -o prova.pdf

The output has one page per voucher, in CSV order, keeping the design's size
and bleed. The QR is drawn as vector shapes (sharp at any size) and encodes
exactly the voucher code the HackEPS scanner expects; the code is also printed
under it in case a camera cannot read it. The design is embedded once (as a
reusable form) and drawn under each QR, so the file stays small.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import segno
from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

MM = 72 / 25.4
CODE_PATTERN = re.compile(r"V[A-HJ-NP-Z2-9]{8}")
# The scanner needs a light margin of a few modules around the code.
QUIET_ZONE_MODULES = 2
# Courier glyphs are 0.6 em wide, so the code can be centred exactly.
COURIER_WIDTH = 0.6
MIN_SIZE_MM = 20


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
) -> bytes:
    """PDF drawing commands for the QR (and code) inside the white square.

    `left`/`top` are the square's top-left corner in PDF points.
    """
    matrix = segno.make(code, error="h", micro=False).matrix
    modules = len(matrix) + 2 * QUIET_ZONE_MODULES
    text_size = size * 0.075 if print_code else 0
    text_gap = text_size * 0.6 if print_code else 0
    qr_side = size - text_size - text_gap
    module = qr_side / modules
    qr_left = left + (size - qr_side) / 2
    qr_top = top
    bottom = top - size

    ops = ["q", "1 g", f"{_fmt(left)} {_fmt(bottom)} {_fmt(size)} {_fmt(size)} re f"]
    ops.append("0 g")
    for row_index, row in enumerate(matrix):
        y = qr_top - (row_index + QUIET_ZONE_MODULES + 1) * module
        col = 0
        while col < len(row):
            if not row[col]:
                col += 1
                continue
            start = col
            while col < len(row) and row[col]:
                col += 1
            x = qr_left + (start + QUIET_ZONE_MODULES) * module
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


def build(
    design: Path,
    codes: list[str],
    output: Path,
    *,
    x_mm: float,
    y_mm: float,
    size_mm: float,
    page_number: int = 1,
    print_code: bool = True,
    outline: bool = False,
) -> int:
    if size_mm < MIN_SIZE_MM:
        raise SystemExit(f"The QR square must be at least {MIN_SIZE_MM} mm wide")
    reader = PdfReader(design)
    if not 1 <= page_number <= len(reader.pages):
        raise SystemExit(f"{design} has {len(reader.pages)} page(s)")
    template = reader.pages[page_number - 1]
    if template.rotation:
        raise SystemExit("Rotated design pages are not supported; export it upright")
    trim = template.trimbox
    left = float(trim.left) + x_mm * MM
    top = float(trim.top) - y_mm * MM
    size = size_mm * MM
    if (
        left < float(trim.left)
        or top > float(trim.top)
        or left + size > float(trim.right)
        or top - size < float(trim.bottom)
    ):
        raise SystemExit("The QR square falls outside the badge (check --x/--y/--size)")

    writer = PdfWriter()
    design_ref = _design_form(writer, template)
    resources = DictionaryObject(
        {
            NameObject("/XObject"): DictionaryObject(
                {NameObject("/Design"): design_ref}
            ),
            NameObject("/Font"): DictionaryObject({NameObject("/FQR"): _font(writer)}),
        }
    )
    resources_ref = writer._add_object(resources)
    for code in codes:
        page = writer.add_blank_page(
            width=float(template.mediabox.width),
            height=float(template.mediabox.height),
        )
        for box in ("/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox"):
            if box in template:
                page[NameObject(box)] = ArrayObject(template[box])
        page[NameObject("/Resources")] = resources_ref
        content = DecodedStreamObject()
        content.set_data(
            b"q /Design Do Q\n"
            + overlay_stream(
                code, left, top, size, print_code=print_code, outline=outline
            )
        )
        page[NameObject("/Contents")] = writer._add_object(content.flate_encode())
    with output.open("wb") as handle:
        writer.write(handle)
    return len(codes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("design", type=Path, help="badge design (PDF)")
    parser.add_argument("csv", type=Path, help="voucher CSV exported from Gestió")
    parser.add_argument("-o", "--output", type=Path, default=Path("acreditacions.pdf"))
    parser.add_argument("--x", type=float, required=True, help="mm from trim left")
    parser.add_argument("--y", type=float, required=True, help="mm from trim top")
    parser.add_argument("--size", type=float, required=True, help="square side, mm")
    parser.add_argument("--page", type=int, default=1, help="design page to use")
    parser.add_argument("--limit", type=int, help="only the first N vouchers")
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
    args = parser.parse_args(argv)

    codes = read_codes(args.csv, args.only_unassigned)
    if args.limit is not None:
        codes = codes[: args.limit]
    if not codes:
        raise SystemExit("No vouchers to print")
    count = build(
        args.design,
        codes,
        args.output,
        x_mm=args.x,
        y_mm=args.y,
        size_mm=args.size,
        page_number=args.page,
        print_code=not args.no_code,
        outline=args.outline,
    )
    print(f"{count} badges written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
