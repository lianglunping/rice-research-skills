"""Test rendered publication figures with synthetic data."""

import os
import sys
from math import hypot
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pytest
from matplotlib.figure import Figure
from PIL import Image
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from publication_style import AXIS_PT, CURVE_PT, ERROR_PT, publication_rc, save_publication_figure


def render_figures(output, font_family):
    with mpl.rc_context(publication_rc(font_family)):
        for name, dimensions in (("py_single", (85, 60)), ("py_multi", (175, 65))):
            panel_count = 1 if name == "py_single" else 2
            fig = Figure(figsize=(7, 5), layout="constrained")
            axs = fig.subplots(1, panel_count, squeeze=False)[0]
            dose = np.array([0, 10, 20])
            response = np.array([2.0, 2.4, 2.2])
            original = response.copy()
            points = axs[0].errorbar(
                dose, response, yerr=0.15, capsize=2,
                ecolor="black", elinewidth=ERROR_PT, capthick=ERROR_PT, ls="-",
                color="#0072B2", marker="o", markersize=3,
            )
            axs[0].set(title="Dose response", xlabel="Dose (Gy)", ylabel="Response")
            assert axs[0].spines["bottom"].get_linewidth() == AXIS_PT
            assert points.lines[0].get_linewidth() == CURVE_PT
            assert points.lines[2][0].get_linewidths()[0] == ERROR_PT
            assert all(cap.get_markeredgewidth() == ERROR_PT for cap in points.lines[1])
            if panel_count == 2:
                for x in ("Group 1", "Group 2"):
                    axs[1].scatter([x] * len(response), response, s=8, color="#0072B2")
                axs[1].set(title="Identical observations", xlabel="Group", ylabel="Response")
                for ax, tag in zip(axs, "AB"):
                    ax.set_title(tag, loc="left", fontsize=9, fontweight="bold")
                for group in axs[1].collections:
                    np.testing.assert_array_equal(group.get_offsets()[:, 1], original)
            np.testing.assert_array_equal(response, original)

            # The export must remain full-size even with a conflicting outer rc setting.
            with mpl.rc_context({"savefig.bbox": "tight"}):
                for extension in ("pdf", "png"):
                    save_publication_figure(fig, output / f"{name}.{extension}", *dimensions)


def assert_artifacts(stem, width_mm, height_mm, expected_text, pdf_tolerance=0.01, dpi=300):
    pages = PdfReader(stem.with_suffix(".pdf")).pages
    assert len(pages) == 1
    page = pages[0]
    assert float(page.mediabox.width) == pytest.approx(width_mm / 25.4 * 72, abs=pdf_tolerance)
    assert float(page.mediabox.height) == pytest.approx(height_mm / 25.4 * 72, abs=pdf_tolerance)
    text = page.extract_text()
    for label in expected_text:
        assert label in text
    assert not page.images

    with Image.open(stem.with_suffix(".png")) as im:
        expected_px = (width_mm / 25.4 * dpi, height_mm / 25.4 * dpi)
        assert im.size == pytest.approx(expected_px, abs=1)
        assert im.info["dpi"] == pytest.approx((dpi, dpi), abs=0.05)
    return page


def test_publication_artifacts(tmp_path):
    # Matplotlib bundles DejaVu Sans. Local review can explicitly exercise Arial.
    family = os.environ.get("FIGURE_TEST_FONT", "DejaVu Sans")
    assert publication_rc()["font.family"] == "Arial"
    render_figures(tmp_path, family)
    for name, dims, text in (
        ("py_single", (85, 60), ("Dose response", "Dose (Gy)", "Response")),
        ("py_multi", (175, 65), ("Dose response", "Identical observations", "Group 1", "Group 2", "A", "B")),
    ):
        page = assert_artifacts(tmp_path / name, *dims, text)
        operations = page.get_contents().operations
        widths = {float(args[0]) for args, op in operations if op == b"w"}
        assert {AXIS_PT, CURVE_PT, ERROR_PT} <= widths
        font_sizes = {float(args[1]) for args, op in operations if op == b"Tf"}
        assert {7, 8} <= font_sizes
        if name == "py_multi":
            assert 9 in font_sizes
        for font_ref in page["/Resources"]["/Font"].values():
            font = font_ref.get_object()
            assert font["/Subtype"] == "/Type0"
            descriptor = font["/DescendantFonts"][0].get_object()["/FontDescriptor"]
            assert "/FontFile2" in descriptor


def stroked_widths(operations):
    # In Quartz, a 1 pt stroke can inherit PDF's default instead of emitting "1 w".
    saved_widths = []
    width = 1
    for args, op in operations:
        if op == b"q":
            saved_widths.append(width)
        elif op == b"Q":
            width = saved_widths.pop()
        elif op == b"w":
            width = float(args[0])
        elif op in {b"S", b"s"}:
            yield width


@pytest.mark.skipif(not os.environ.get("FIGURE_R_ARTIFACT_DIR"), reason="R artifacts not requested")
def test_r_publication_artifacts():
    output = Path(os.environ["FIGURE_R_ARTIFACT_DIR"])
    tolerance = 0.01 if os.environ.get("FIGURE_TEST_PDF_DEVICE") == "quartz" else 1.0
    for name, dims, text in (
        ("r_single", (85, 60), ("Dose response", "Dose (Gy)", "Response")),
        ("r_group", (85, 60), ("Identical observations", "Group 1", "Group 2")),
        ("r_multi", (175, 65), ("Dose response", "Identical observations", "A", "B")),
    ):
        page = assert_artifacts(output / name, *dims, text, pdf_tolerance=tolerance)
        operations = page.get_contents().operations
        widths = list(stroked_widths(operations))
        assert any(w == pytest.approx(AXIS_PT, abs=0.01) for w in widths)
        if name != "r_group":
            assert any(w == pytest.approx(CURVE_PT, abs=0.01) for w in widths)
        font_sizes = []

        def record_font_size(text, cm, tm, _font, size):
            if text.strip():
                # Either the font setting or the text transform can carry the point size.
                x = tm[2] * cm[0] + tm[3] * cm[2]
                y = tm[2] * cm[1] + tm[3] * cm[3]
                font_sizes.append(size * hypot(x, y))

        page.extract_text(visitor_text=record_font_size)
        expected_sizes = (7, 8, 9) if name == "r_multi" else (7, 8)
        for size in expected_sizes:
            assert any(entry == pytest.approx(size, abs=0.01) for entry in font_sizes)
        for font_ref in page["/Resources"]["/Font"].values():
            font = font_ref.get_object()
            assert font["/Subtype"] != "/Type3"
            if font["/Subtype"] == "/Type0":
                font = font["/DescendantFonts"][0].get_object()
            assert any(key in font["/FontDescriptor"] for key in ("/FontFile", "/FontFile2", "/FontFile3"))


@pytest.mark.parametrize("filename,dims", [
    ("invalid.jpg", (85, 60)),
    ("invalid.pdf", (0, 60)),
    ("invalid.png", (85, float("nan"))),
])
def test_invalid_export(tmp_path, filename, dims):
    output = tmp_path / filename
    with pytest.raises(ValueError):
        save_publication_figure(Figure(), output, *dims)
    assert not output.exists()


if __name__ == "__main__":
    # Explicit previews for manual inspection. Pytest always uses its own temp directory.
    output_dir = Path(sys.argv[1])
    render_figures(output_dir, os.environ.get("FIGURE_TEST_FONT", "Arial"))
