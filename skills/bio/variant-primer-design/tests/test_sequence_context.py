from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sequence_context import attach_sequence_context, normalize_variant_table  # noqa: E402


def test_normalize_variant_table_accepts_chinese_columns() -> None:
    df = pd.DataFrame(
        [
            {
                "名称": "H1-2",
                "CHROM": "Chr07",
                "POS": 1833501,
                "REF": "C",
                "ALT": "CA",
                "extra_note": "keep",
            }
        ]
    )

    normalized = normalize_variant_table(df)

    assert normalized.loc[0, "name"] == "H1-2"
    assert normalized.loc[0, "chrom"] == "Chr07"
    assert normalized.loc[0, "pos"] == 1833501
    assert normalized.loc[0, "variant_type"] == "InDel"
    assert normalized.loc[0, "extra_note"] == "keep"


def test_attach_sequence_context_builds_full_seq(tmp_path: Path) -> None:
    fasta_path = tmp_path / "reference.fa"
    fasta_path.write_text(">Chr01\nACGTACGTACGTACGTACGT\n", encoding="utf-8")

    df = pd.DataFrame(
        [
            {
                "name": "demo",
                "chrom": "Chr01",
                "pos": 5,
                "ref": "A",
                "alt": "G",
            }
        ]
    )

    attached = attach_sequence_context(df, reference_fasta=fasta_path, flank_size=4, assume_left_flank=4)

    assert attached.loc[0, "full_seq"] == "ACGTACGTA"
    assert attached.loc[0, "left_flank_len"] == 4
    assert bool(attached.loc[0, "ref_matches_reference"]) is True
