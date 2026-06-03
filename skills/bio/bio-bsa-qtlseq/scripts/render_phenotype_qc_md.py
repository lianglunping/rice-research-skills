#!/usr/bin/env python3
"""render_phenotype_qc_md.py — 把 phenotype_qc.json 渲染成 markdown"""
import argparse, json, sys

ap = argparse.ArgumentParser()
ap.add_argument('--json', required=True)
args = ap.parse_args()

d = json.load(open(args.json))

print(f"# Phenotype QC (多时间点对比前置)")
print()
print(f"**Comparability**: `{d['comparable']}`")
print()
print("## 样本交集")
print(f"- T1 样本数: {d['t1_samples']}")
print(f"- T2 样本数: {d['t2_samples']}")
print(f"- 共享样本: {d['shared_samples']} ({d['shared_ratio']:.1%})")
print()
print("## Metadata 一致性")
print(f"- unit_match: {d['unit_match']}")
print(f"- batch_match: {d['batch_match']}")
print(f"- method_match: {d['method_match']}")
print()
if d['reasons']:
    print("## Blocker 原因")
    for r in d['reasons']: print(f"- {r}")
    print()
if d['warnings']:
    print("## 警告")
    for w in d['warnings']: print(f"- {w}")
    print()
print("## 解读建议")
if d['comparable'] == 'full':
    print("两时间点完全可比, 允许共识 QTL 生物学解读")
elif d['comparable'] == 'interval_only':
    print("仅 interval 级别可比, **禁止**跨时间点生物学解读; 仅输出区间 overlap 供 QC")
else:
    print("**不可比** (unit/方法差异过大), 不执行任何跨时间点对比")
