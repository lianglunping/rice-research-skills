from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.primer_core import PrimerConstraints, PrimerDesigner, VariantRecord  # noqa: E402


def test_design_variant_respects_left_flank_length() -> None:
    forward_seq = "CGGTAGGAAGTAACCACACCGG"
    reverse_seq = "ATGGTTGTGTGGCGTGGAGAGC"
    reverse_template = PrimerDesigner.reverse_complement(reverse_seq)

    left_padding = "AT" * 20
    between_forward_and_variant = "AT" * 59
    between_variant_and_reverse = "AT" * 73 + "A"
    right_padding = "AT" * 30

    full_seq = (
        left_padding
        + forward_seq
        + between_forward_and_variant
        + "CAG"
        + between_variant_and_reverse
        + reverse_template
        + right_padding
    )

    record = VariantRecord(
        name="demo_indel",
        chrom="chrSynthetic",
        pos=181,
        ref="CAG",
        alt="C",
        full_seq=full_seq,
        left_flank_len=180,
        variant_type="InDel",
    )

    designer = PrimerDesigner(PrimerConstraints.strict())
    result = designer.design_variant(record, "strict")

    assert result["status"] == "SUCCESS"
    assert result["forward_seq"] == forward_seq
    assert result["reverse_seq"] == reverse_seq
    assert result["product_wt"] == 312
    assert result["product_mt"] == 310
