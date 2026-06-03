#!/usr/bin/env python3
"""phenotype_qc.py — 多时间点 phenotype metadata QC 前置比较 (盲点 #5)

Usage:
    python phenotype_qc.py --t1 samples_t1.tsv --t1-meta meta_t1.yaml
                           --t2 samples_t2.tsv --t2-meta meta_t2.yaml
                           --out compare_phenotype_qc.json

输出 JSON:
    {
      "comparable": "full" | "interval_only" | "not_comparable",
      "reasons": [...],
      "t1_samples": N, "t2_samples": N, "shared_samples": N,
      "shared_ratio": float,
      "unit_match": bool, "batch_match": bool, "method_match": bool,
      "warnings": [...]
    }
"""
import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERR] 缺 pyyaml", file=sys.stderr); sys.exit(4)


def read_samples(path):
    samples = {}
    with open(path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row['sample_id'].startswith('#'): continue
            if row['bulk'] in ('HighBulk', 'LowBulk'):
                samples[row['sample_id']] = row['bulk']
    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--t1', required=True); ap.add_argument('--t1-meta', required=True)
    ap.add_argument('--t2', required=True); ap.add_argument('--t2-meta', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    s1 = read_samples(args.t1)
    s2 = read_samples(args.t2)

    shared = set(s1) & set(s2)
    shared_ratio = len(shared) / max(len(s1), len(s2)) if s1 and s2 else 0

    m1 = yaml.safe_load(open(args.t1_meta)) if Path(args.t1_meta).exists() else {}
    m2 = yaml.safe_load(open(args.t2_meta)) if Path(args.t2_meta).exists() else {}

    unit_match = m1.get('unit') == m2.get('unit')
    batch_match = m1.get('batch') == m2.get('batch')
    method_match = m1.get('measurement_method') == m2.get('measurement_method')

    reasons = []
    warnings = []

    if not unit_match: reasons.append(f"phenotype_unit mismatch: {m1.get('unit')} vs {m2.get('unit')}")
    if not method_match: warnings.append("measurement_method 不一致, 建议先确认测定口径")
    if not batch_match: warnings.append(f"batch 不同 ({m1.get('batch')} vs {m2.get('batch')}), 不做跨批次生物学解读")

    if shared_ratio < 0.5:
        warnings.append(f"shared_ratio={shared_ratio:.2f} < 0.5, 对 interval 比较仍可用但不建议跨时间点解读")

    # Decision
    if not unit_match:
        comparable = "not_comparable"
    elif shared_ratio < 0.5 or not method_match or not batch_match:
        comparable = "interval_only"
    else:
        comparable = "full"

    out = {
        "comparable": comparable,
        "reasons": reasons,
        "warnings": warnings,
        "t1_samples": len(s1),
        "t2_samples": len(s2),
        "shared_samples": len(shared),
        "shared_ratio": round(shared_ratio, 3),
        "unit_match": unit_match,
        "batch_match": batch_match,
        "method_match": method_match,
        "t1_meta": m1,
        "t2_meta": m2,
    }
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    print(f"[OK] phenotype_qc: comparable={comparable}, shared={shared_ratio:.2%}", file=sys.stderr)


if __name__ == '__main__':
    main()
