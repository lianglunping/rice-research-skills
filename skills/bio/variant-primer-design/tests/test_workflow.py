from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_end_to_end_workflow(tmp_path: Path) -> None:
    forward_seq = "CGGTAGGAAGTAACCACACCGG"
    reverse_seq = "ATGGTTGTGTGGCGTGGAGAGC"
    reverse_template = reverse_seq.translate(str.maketrans("ATCG", "TAGC"))[::-1]

    full_seq = (
        ("AT" * 20)
        + forward_seq
        + ("AT" * 59)
        + "CAG"
        + (("AT" * 73) + "A")
        + reverse_template
        + ("AT" * 30)
    )

    reference_fasta = tmp_path / "reference.fa"
    reference_fasta.write_text(f">chrSynthetic\n{full_seq}\n", encoding="utf-8")

    input_path = tmp_path / "variants.tsv"
    pd.DataFrame(
        [
            {
                "name": "demo_indel",
                "CHROM": "chrSynthetic",
                "POS": 181,
                "REF": "CAG",
                "ALT": "C",
            }
        ]
    ).to_csv(input_path, sep="\t", index=False)

    output_dir = tmp_path / "results"
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_primer_workflow.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(input_path),
        "--reference-fasta",
        str(reference_fasta),
        "--assay-mode",
        "indel_pcr",
        "--output-dir",
        str(output_dir),
        "--threads",
        "1",
    ]

    subprocess.run(cmd, check=True)

    final_table = pd.read_csv(output_dir / "final_primers.tsv", sep="\t")
    assert final_table.loc[0, "status"] == "SUCCESS"
    assert final_table.loc[0, "specificity_status"] == "specific"
    assert (output_dir / "primer_specificity.tsv").exists()
    assert (output_dir / "primer_order.tsv").exists()
    assert (output_dir / "design_report.txt").exists()
