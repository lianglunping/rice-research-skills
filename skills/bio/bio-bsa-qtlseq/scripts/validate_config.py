#!/usr/bin/env python3
"""validate_config.py — BSA bsa.yaml + profile.yaml 校验器

Usage:
    python validate_config.py --config bsa.yaml [--profile grape-vvinifera-phytozome]
                              [--schema-dir ~/.codex/skills/bio-bsa-qtlseq/schemas]
                              [--out merged_config.yaml]

Exit codes:
    0 = 全通过
    2 = JSON Schema 校验错
    3 = 语义错（文件不存在、样本不匹配等）
    4 = 依赖错（工具缺失、env 错）

依赖: pyyaml, jsonschema（在 environment.yml 锁定）
"""
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import Draft7Validator
except ImportError as e:
    print(f"[ERR] 缺依赖: {e}. 安装: pip install pyyaml jsonschema", file=sys.stderr)
    sys.exit(4)


def deep_merge(base: dict, over: dict) -> dict:
    """profile 与 project 的 deep-merge. project 字段覆盖 profile."""
    out = dict(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def validate_against(data: dict, schema_path: Path, label: str) -> list[str]:
    with open(schema_path) as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return [f"[{label}] {'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]


def semantic_checks(cfg: dict) -> list[str]:
    """语义级检查（schema 之外的业务逻辑）."""
    errs = []
    # 1. 文件存在性
    for fkey in [('reference', 'fa_path'), ('reference', 'gff3_path'),
                 ('variant_source', 'cohort_vcf'), ('phenotype', 'phenotype_file')]:
        val = cfg.get(fkey[0], {}).get(fkey[1])
        if val and not Path(val).exists():
            errs.append(f"[semantic] {'.'.join(fkey)} 文件不存在: {val}")

    # 2. chrom_list vs chrom_regex 一致性（若都指定）
    ref = cfg.get('reference', {})
    if ref.get('chrom_regex') and ref.get('chrom_list'):
        import re
        pat = re.compile(ref['chrom_regex'])
        for c in ref['chrom_list']:
            if not pat.match(c):
                errs.append(f"[semantic] chrom_list 中 '{c}' 不匹配 chrom_regex '{ref['chrom_regex']}'")

    # 3. bulk_size 警告（不是错误）
    bs = cfg.get('population', {}).get('bulk_size', [])
    if bs and min(bs) < 20:
        print(f"[WARN] bulk_size {bs} < 20, LIMITATIONS 将自动标注小样本风险", file=sys.stderr)

    # 4. thresholds 合理性
    gprime = cfg.get('pipeline', {}).get('thresholds', {}).get('Gprime', [])
    if gprime and (gprime[0] >= gprime[1]):
        errs.append(f"[semantic] thresholds.Gprime preplanned {gprime[0]} 应 < fallback {gprime[1]}")

    # 5. gene_id_prefix 只能是文档示例, 不能被脚本依赖
    gip = ref.get('gene_id_prefix')
    if gip:
        print(f"[INFO] gene_id_prefix='{gip}' 仅文档举例用, 不参与解析", file=sys.stderr)

    return errs


def validate_samples_tsv(tsv_path: Path, schema_path: Path) -> list[str]:
    """samples.tsv row-by-row 校验 (Round 1 Fix: 接入 samples.schema.json)."""
    if not tsv_path.exists():
        return [f"[semantic] samples.tsv 不存在: {tsv_path}"]
    with open(schema_path) as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    errs = []
    import csv
    with open(tsv_path) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader, start=2):  # row 2 = 首条数据
            if row.get('sample_id', '').startswith('#'): continue
            # 类型转换
            if row.get('phenotype_value') and row['phenotype_value'] not in ('NA', 'N/A', '-', ''):
                try: row['phenotype_value'] = float(row['phenotype_value'])
                except ValueError: pass
            for e in validator.iter_errors(row):
                errs.append(f"[samples row {i}] {e.message}")
    return errs


def validate_phenotype_meta(meta_path: Path, schema_path: Path) -> list[str]:
    """phenotype_source.meta.yaml 校验 (Round 1 Fix: 接入 phenotype-meta.schema.json)."""
    if not meta_path.exists():
        return []  # 可选文件
    with open(meta_path) as f:
        data = yaml.safe_load(f) or {}
    with open(schema_path) as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    return [f"[phenotype-meta] {'.'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--profile')
    ap.add_argument('--schema-dir', default=str(Path(__file__).parent.parent / 'schemas'))
    ap.add_argument('--profile-dir', default=str(Path(__file__).parent.parent / 'profiles'))
    ap.add_argument('--samples', help='samples.tsv 路径（可选, 存在则校验）')
    ap.add_argument('--phenotype-meta', help='phenotype_source.meta.yaml 路径（可选, 存在则校验）')
    ap.add_argument('--out')
    args = ap.parse_args()

    schema_dir = Path(args.schema_dir)

    # 1. Profile validation（若指定）
    merged = {}
    if args.profile:
        profile_path = Path(args.profile_dir) / f"{args.profile}.yaml"
        if not profile_path.exists():
            # 允许直接给路径
            profile_path = Path(args.profile)
        if not profile_path.exists():
            print(f"[ERR] profile 不存在: {args.profile}", file=sys.stderr)
            sys.exit(3)
        prof = load_yaml(profile_path)
        prof_errs = validate_against(prof, schema_dir / 'profile.schema.json', 'profile')
        if prof_errs:
            for e in prof_errs:
                print(e, file=sys.stderr)
            sys.exit(2)
        merged = deep_merge(merged, prof)

    # 2. Project config
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"[ERR] config 不存在: {cfg_path}", file=sys.stderr)
        sys.exit(3)
    proj = load_yaml(cfg_path)
    merged = deep_merge(merged, proj)

    # 3. Merged config validation
    proj_errs = validate_against(merged, schema_dir / 'bsa-config.schema.json', 'merged')
    if proj_errs:
        for e in proj_errs:
            print(e, file=sys.stderr)
        sys.exit(2)

    # 4. Semantic checks
    sem_errs = semantic_checks(merged)
    if sem_errs:
        for e in sem_errs:
            print(e, file=sys.stderr)
        sys.exit(3)

    # 4b. samples.tsv 校验 (Round 1 Fix)
    if args.samples:
        samples_errs = validate_samples_tsv(Path(args.samples), schema_dir / 'samples.schema.json')
        if samples_errs:
            for e in samples_errs[:20]:  # 前 20 条
                print(e, file=sys.stderr)
            sys.exit(3)
        print(f"[OK] samples.tsv 校验通过", file=sys.stderr)

    # 4c. phenotype meta 校验 (Round 1 Fix)
    if args.phenotype_meta:
        meta_errs = validate_phenotype_meta(Path(args.phenotype_meta), schema_dir / 'phenotype-meta.schema.json')
        if meta_errs:
            for e in meta_errs:
                print(e, file=sys.stderr)
            sys.exit(3)
        print(f"[OK] phenotype_source.meta.yaml 校验通过", file=sys.stderr)

    # 5. Output merged
    if args.out:
        with open(args.out, 'w') as f:
            yaml.safe_dump(merged, f, default_flow_style=False, allow_unicode=True)
        print(f"[OK] 配置校验通过, merged 已写入 {args.out}", file=sys.stderr)
    else:
        yaml.safe_dump(merged, sys.stdout, default_flow_style=False, allow_unicode=True)
        print("[OK] 配置校验通过", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
