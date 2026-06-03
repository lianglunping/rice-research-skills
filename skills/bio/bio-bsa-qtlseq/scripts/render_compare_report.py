#!/usr/bin/env python3
"""render_compare_report.py — 生成多时间点对比汇总 markdown"""
import argparse, sys, os
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--intervals', required=True, help='dir containing *_shared.tsv etc')
ap.add_argument('--phenotype_qc', required=True)
ap.add_argument('--comparable', required=True)
ap.add_argument('--out', required=True)
args = ap.parse_args()

d = Path(args.intervals)
lines = []
lines.append("# 多时间点 QTL 对比汇总\n")
lines.append(f"Comparability: `{args.comparable}`\n")
lines.append("## 1. Phenotype QC\n")
lines.append(open(args.phenotype_qc).read())
lines.append("\n## 2. 区间交集/差集\n")
for f in sorted(d.glob('*_shared.tsv')) + sorted(d.glob('*_only.tsv')):
    n = sum(1 for _ in open(f))
    lines.append(f"- `{f.name}`: {n} regions")

if args.comparable == 'full':
    lines.append("\n## 3. 共识 QTL 建议\n")
    lines.append("两时间点均显著的区间为**最高置信**候选，优先做 KASP 精细定位。")
else:
    lines.append("\n> **注**: 因可比性限制，不做跨时间点生物学解读。")

Path(args.out).write_text('\n'.join(lines))
print(f"[OK] compare_report.md 已生成", file=sys.stderr)
