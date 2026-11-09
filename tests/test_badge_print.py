import csv

import pytest
import segno
from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, RectangleObject

from scripts.badge_print import MM, build, overlay_stream, read_codes

CODES = ["VABCDEFGH", "V23456789", "VKMNPQRST"]


def design(path, bleed=3):
    width, height = 85 + 2 * bleed, 125 + 2 * bleed
    page = PageObject.create_blank_page(width=width * MM, height=height * MM)
    page[NameObject("/TrimBox")] = RectangleObject(
        [bleed * MM, bleed * MM, (85 + bleed) * MM, (125 + bleed) * MM]
    )
    content = DecodedStreamObject()
    content.set_data(b"0.1 0.1 0.4 rg 0 0 300 400 re f")
    page[NameObject("/Contents")] = content
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(path)
    return path


def voucher_csv(path, codes, assigned=()):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["code", "hacker_id", "hacker_name", "assigned_at"])
        for code in codes:
            writer.writerow([code, "7" if code in assigned else "", "", ""])
    return path


def test_every_badge_keeps_the_design_and_gets_its_own_code(tmp_path):
    output = tmp_path / "badges.pdf"
    build(
        design(tmp_path / "design.pdf"), CODES, output, x_mm=27.5, y_mm=70, size_mm=30
    )
    reader = PdfReader(output)
    assert len(reader.pages) == len(CODES)
    design_refs = set()
    for page, code in zip(reader.pages, CODES, strict=True):
        content = page.get_contents().get_data()
        assert content.startswith(b"q /Design Do Q")
        assert f"({code}) Tj".encode() in content
        assert [c for c in CODES if f"({c})".encode() in content] == [code]
        design_refs.add(page["/Resources"]["/XObject"].raw_get("/Design").idnum)
        # Bleed and trim are preserved for the print shop.
        assert page.trimbox == reader.pages[0].trimbox
        assert page.mediabox.width == pytest.approx(91 * MM)
    # The design is embedded once, not copied into every page.
    assert len(design_refs) == 1
    form = reader.pages[0]["/Resources"]["/XObject"]["/Design"]
    assert b"re f" in form.get_data()


def test_qr_modules_match_the_voucher_code():
    matrix = segno.make("VABCDEFGH", error="h", micro=False).matrix
    dark = sum(sum(1 for cell in row if cell) for row in matrix)
    stream = overlay_stream("VABCDEFGH", 100, 300, 85, print_code=False).decode()
    rectangles = stream.count(" re\n") + stream.count(" re\nf")
    # Horizontal runs are merged, so there are fewer rectangles than modules.
    assert 0 < rectangles <= dark
    assert "Tj" not in stream


def test_square_outside_the_badge_is_rejected(tmp_path):
    with pytest.raises(SystemExit, match="outside"):
        build(
            design(tmp_path / "design.pdf"),
            CODES,
            tmp_path / "out.pdf",
            x_mm=70,
            y_mm=70,
            size_mm=30,
        )
    with pytest.raises(SystemExit, match="at least"):
        build(
            design(tmp_path / "design.pdf"),
            CODES,
            tmp_path / "out.pdf",
            x_mm=10,
            y_mm=10,
            size_mm=10,
        )


def test_csv_validation(tmp_path):
    path = voucher_csv(tmp_path / "v.csv", CODES, assigned={"V23456789"})
    assert read_codes(path) == CODES
    assert read_codes(path, only_unassigned=True) == ["VABCDEFGH", "VKMNPQRST"]
    with pytest.raises(SystemExit, match="Duplicated"):
        read_codes(voucher_csv(tmp_path / "d.csv", [*CODES, CODES[0]]))
    with pytest.raises(SystemExit, match="Invalid"):
        read_codes(voucher_csv(tmp_path / "i.csv", ["VO0I1XXXX"]))
