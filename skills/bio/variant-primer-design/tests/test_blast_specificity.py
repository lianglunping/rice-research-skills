from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.blast_specificity import summarize_primer_hits  # noqa: E402


def test_summarize_primer_hits_filters_by_identity_and_coverage(tmp_path: Path) -> None:
    blast_path = tmp_path / "mock_blast.tsv"
    blast_path.write_text(
        "\n".join(
            [
                "F1\tchr1\t100.0\t22\t22\t1\t22\t0\t0\t1e-10\t44.0",
                "F1\tchr2\t93.0\t22\t22\t1\t22\t0\t0\t1e-05\t40.0",
                "R1\tchr1\t99.0\t20\t22\t1\t20\t0\t0\t1e-06\t39.0",
                "R1\tchr3\t100.0\t22\t22\t1\t22\t0\t0\t1e-11\t45.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = summarize_primer_hits(blast_path, min_identity=95.0, min_coverage=0.95)
    hit_map = dict(zip(summary["qseqid"], summary["hit_count"]))

    assert hit_map["F1"] == 1
    assert hit_map["R1"] == 1
