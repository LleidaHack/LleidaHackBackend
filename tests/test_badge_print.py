import csv

import pytest
import segno
from PIL import Image
from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, RectangleObject

from scripts.badge_print import MM, build, load_design, main, overlay_stream, read_codes

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
        load_design(design(tmp_path / "design.pdf")),
        CODES,
        output,
        x=27.5,
        y=70,
        size=30,
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
            load_design(design(tmp_path / "design.pdf")),
            CODES,
            tmp_path / "out.pdf",
            x=70,
            y=70,
            size=30,
        )
    with pytest.raises(SystemExit, match="at least"):
        build(
            load_design(design(tmp_path / "design.pdf")),
            CODES,
            tmp_path / "out.pdf",
            x=10,
            y=10,
            size=10,
        )


def test_csv_validation(tmp_path):
    path = voucher_csv(tmp_path / "v.csv", CODES, assigned={"V23456789"})
    assert read_codes(path) == CODES
    assert read_codes(path, only_unassigned=True) == ["VABCDEFGH", "VKMNPQRST"]
    with pytest.raises(SystemExit, match="Duplicated"):
        read_codes(voucher_csv(tmp_path / "d.csv", [*CODES, CODES[0]]))
    with pytest.raises(SystemExit, match="Invalid"):
        read_codes(voucher_csv(tmp_path / "i.csv", ["VO0I1XXXX"]))


def test_artwork_images_get_bleed_back_pages_and_slices(tmp_path):
    front, back = tmp_path / "front.png", tmp_path / "back.png"
    Image.new("RGB", (1000, 1573), (41, 41, 41)).save(front)
    Image.new("RGB", (1000, 1573), (200, 60, 60)).save(back)
    codes = voucher_csv(tmp_path / "v.csv", CODES)
    output = tmp_path / "badges.pdf"
    main(
        [
            str(front),
            str(codes),
            "--back",
            str(back),
            "--width-mm",
            "90",
            "--x",
            "126",
            "--y",
            "949",
            "--size",
            "269",
            "--skip",
            "1",
            "--limit",
            "2",
            "-o",
            str(output),
        ]
    )
    reader = PdfReader(output)
    assert len(reader.pages) == 4
    fronts, backs = reader.pages[0::2], reader.pages[1::2]
    for page, code in zip(fronts, CODES[1:], strict=True):
        assert f"({code}) Tj".encode() in page.get_contents().get_data()
    for page in backs:
        assert page.get_contents().get_data() == b"q /Design Do Q"
    trim, media = fronts[0].trimbox, fronts[0].mediabox
    assert float(trim.width) == pytest.approx(90 * MM)
    assert float(trim.left) == pytest.approx(3 * MM, abs=0.3)
    assert float(media.width) == pytest.approx(96 * MM, abs=0.6)
    # Front and back artwork are each embedded once.
    designs = {
        p["/Resources"]["/XObject"].raw_get("/Design").idnum for p in reader.pages
    }
    assert len(designs) == 2


def test_slices_cannot_run_past_the_generated_vouchers(tmp_path):
    front = tmp_path / "front.png"
    Image.new("RGB", (1000, 1573), (41, 41, 41)).save(front)
    codes = voucher_csv(tmp_path / "v.csv", CODES)
    args = [str(front), str(codes), "--width-mm", "90", "--x", "126", "--y", "949"]
    with pytest.raises(SystemExit, match="Only 1 vouchers left"):
        main([*args, "--size", "269", "--skip", "2", "--limit", "5"])
    with pytest.raises(SystemExit, match="at least 18 mm"):
        main([*args, "--size", "150", "-o", str(tmp_path / "o.pdf")])


def test_qr_can_fill_a_rounded_square_without_painting_over_it():
    stream = overlay_stream(
        "VABCDEFGH", 100, 300, 80, print_code=False, quiet_zone=1, fill=False
    ).decode()
    assert "1 g" not in stream and "Tj" not in stream
    matrix = segno.make("VABCDEFGH", error="h", micro=False).matrix
    module = 80 / (len(matrix) + 2)
    # The first dark module starts one module inside the square.
    first = next(line for line in stream.splitlines() if line.endswith(" re"))
    assert float(first.split()[0]) == pytest.approx(100 + module, abs=0.01)


def test_rounded_eyes_and_fixed_masks(tmp_path):
    from scripts.badge_print import read_masks

    plain = overlay_stream("VABCDEFGH", 100, 300, 80, print_code=False, mask=3)
    rounded = overlay_stream(
        "VABCDEFGH", 100, 300, 80, print_code=False, mask=3, rounded_eyes=True
    )
    # Three finder patterns: an even-odd ring plus a centre each, drawn as curves.
    assert rounded.count(b"f*") == 3 and b" c\n" in rounded and b" c\n" not in plain
    assert overlay_stream("VABCDEFGH", 100, 300, 80, mask=3) != overlay_stream(
        "VABCDEFGH", 100, 300, 80, mask=5
    )
    masks = tmp_path / "m.csv"
    masks.write_text("code,mask\nVABCDEFGH,3\n")
    assert read_masks(masks, ["VABCDEFGH"]) == {"VABCDEFGH": 3}
    with pytest.raises(SystemExit, match="No verified mask"):
        read_masks(masks, ["VABCDEFGH", "V23456789"])
