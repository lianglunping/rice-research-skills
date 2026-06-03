#!/usr/bin/env bash
# pre_delivery_check.sh — Gate 4 机器可判定项自动核验 (10 项)
# Usage: pre_delivery_check.sh <release_dir>
# Exit: 0 = 全 PASS; 1 = 存在 FAIL (进入 FIX_LOOP 或人工处理)

set -eo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <release_dir>" >&2; exit 2
fi

REL="$1"
cd "$REL" || { echo "[ERR] $REL 不存在" >&2; exit 2; }

FAIL=0
log() { echo "[$(date +%T)] $*"; }
check() {
    local name=$1; shift
    log "Check: $name"
    if "$@"; then
        log "  PASS"
    else
        log "  FAIL"
        FAIL=$((FAIL+1))
    fi
}

# === Check 1: MANIFEST.md5 完整性 ===
check_manifest() {
    [ -f MANIFEST.md5 ] || return 1
    find . -type f ! -name 'MANIFEST.md5' ! -name 'MANIFEST.sha256' | sort > /tmp/actual.txt
    grep -v '^#' MANIFEST.md5 | awk '{print $2}' | sort > /tmp/manifest.txt
    diff -q /tmp/actual.txt /tmp/manifest.txt > /dev/null
}
check "1/10 MANIFEST.md5 覆盖所有文件" check_manifest

# === Check 2: 无内部路径残留 ===
check_no_hardcode() {
    ! grep -rn 'sxyH3\|/home/[a-z0-9]*/\|conda activate ngs' --include='*.md' --include='*.sh' --include='*.py' --include='*.R' --include='*.yml' --include='*.yaml' .
}
check "2/10 无硬编码服务器路径" check_no_hardcode

# === Check 3: README 关键数字可由 TSV 重算 ===
check_readme_numbers() {
    local q005_file="results/main/Gprime_q005_regions.tsv"
    local ci95_file="results/main/QTLseq_ci95_regions.tsv"
    [ -f "$q005_file" ] || return 1

    local ACTUAL_Q005=$(($(wc -l < "$q005_file") - 1))
    local README_Q005=$(grep -oE '\*\*[0-9]+\*\* 候选 QTL|\*\*[0-9]+\*\* Gprime' 00_README.md 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1)
    if [ -n "$README_Q005" ] && [ "$README_Q005" -ne "$ACTUAL_Q005" ]; then
        log "  README Gprime q005=$README_Q005 vs TSV=$ACTUAL_Q005"
        return 1
    fi

    if [ -f "$ci95_file" ]; then
        local ACTUAL_CI95=$(($(wc -l < "$ci95_file") - 1))
        local README_CI95=$(grep -oE '\*\*[0-9]+\*\* 精细化' 00_README.md 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1)
        if [ -n "$README_CI95" ] && [ "$README_CI95" -ne "$ACTUAL_CI95" ]; then
            log "  README QTLseq ci95=$README_CI95 vs TSV=$ACTUAL_CI95"
            return 1
        fi
    fi
    return 0
}
check "3/10 README 数字可重算 (TSV 核对)" check_readme_numbers

# === Check 4: Tier 分级按 meanQval ===
check_tier() {
    local f="results/main/Gprime_q005_regions.tsv"
    [ -f "$f" ] || return 0  # 无数据则跳过
    local A_ACTUAL=$(awk -F'\t' 'NR>1 && $17<0.025' "$f" | wc -l | tr -d ' ')
    local TIER_A_CLAIM=$(grep -oE 'A 级.*?[0-9]+' Top_QTL_annotated.md 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1)
    if [ -n "$TIER_A_CLAIM" ] && [ "$TIER_A_CLAIM" -ne "$A_ACTUAL" ]; then
        log "  Tier A claim=$TIER_A_CLAIM vs 实际 meanQval<0.025=$A_ACTUAL"
        return 1
    fi
    return 0
}
check "4/10 Tier 分级一致性" check_tier

# === Check 5: Top QTL 基因数一致 ===
check_top_qtl_genes() {
    local cg_file="results/main/QTLseq_ci95_regions_candidate_genes.tsv"
    [ -f "$cg_file" ] || return 0
    # 抽检 qtl6 (chr5 最强候选) 的基因数
    local ACTUAL=$(awk -F'\t' '$4 ~ /qtl6/' "$cg_file" | cut -f8 | sort -u | wc -l | tr -d ' ')
    # README 或 Top_QTL 里提到的 qtl6 基因数
    local CLAIMED=$(grep -oE 'qtl6.*?[0-9]+ 基因' Top_QTL_annotated.md 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1)
    if [ -n "$CLAIMED" ] && [ -n "$ACTUAL" ] && [ "$CLAIMED" -ne "$ACTUAL" ]; then
        log "  qtl6 基因数 claim=$CLAIMED vs 实测=$ACTUAL"
        return 1
    fi
    return 0
}
check "5/10 Top QTL 基因数一致 (bedtools 实测)" check_top_qtl_genes

# === Check 6: SUMMARY 含 4×3 矩阵 ===
check_summary_matrix() {
    local s="results/main/SUMMARY_v2.md"
    [ -f "$s" ] || return 1
    grep -q 'Gprime q001' "$s" && grep -q 'Gprime q005' "$s" && \
        grep -q 'QTLseq ci99' "$s" && grep -q 'QTLseq ci95' "$s" && \
        grep -q 'w500k\|window=500' "$s" && grep -q 'rf035\|refAF=0.35' "$s"
}
check "6/10 SUMMARY 4×3 矩阵" check_summary_matrix

# === Check 7: 必需文件 + PDF/PNG 成对 ===
check_required() {
    local REQ=(00_README.md 01_METHODS.md 02_LIMITATIONS.md 03_COLUMN_DEFINITIONS.md
               HOWTO_GO_KEGG.md Top_QTL_annotated.md VERSION CHANGELOG.md
               MANIFEST.md5 MANIFEST.sha256
               results/main/SUMMARY_v2.md figures/README.md
               metadata/samples.tsv metadata/parameters.yaml
               metadata/environment.yml metadata/software_versions.txt)
    for f in "${REQ[@]}"; do
        [ -f "$f" ] || { log "  missing: $f"; return 1; }
    done
    # PDF/PNG 成对
    for pdf in figures/*.pdf; do
        [ -f "${pdf%.pdf}.png" ] || { log "  missing PNG for $pdf"; return 1; }
    done
    return 0
}
check "7/10 必需文件 + PDF/PNG 成对" check_required

# === Check 8: QTLseqr 版本锁定 ===
check_qtlseqr_lock() {
    grep -qE 'QTLseqr[[:space:]]+0\.7\.5\.2' metadata/software_versions.txt
}
check "8/10 QTLseqr 版本锁定" check_qtlseqr_lock

# === Check 9: SHA256 校验 ===
check_sha256() {
    [ -f MANIFEST.sha256 ] || return 1
    sha256sum -c MANIFEST.sha256 > /dev/null 2>&1
}
check "9/10 SHA256 manifest 校验" check_sha256

# === Check 10: gene_id_prefix 仅在 docs 出现 ===
check_gene_id_prefix_docs() {
    # 提取 parameters.yaml 中的 gene_id_prefix
    local gip=$(grep -oE 'gene_id_prefix:\s*"[^"]+"' metadata/parameters.yaml 2>/dev/null | head -1 | grep -oE '"[^"]+"' | tr -d '"')
    [ -z "$gip" ] && return 0   # 未定义即 pass
    # 检查: 脚本中不能用这个前缀
    if grep -rn "$gip" scripts/ 2>/dev/null; then
        log "  脚本中出现 gene_id_prefix=$gip (应仅在 docs 出现)"
        return 1
    fi
    return 0
}
check "10/10 gene_id_prefix x-doc-only" check_gene_id_prefix_docs

# === 汇总 ===
log "================================"
if [ $FAIL -eq 0 ]; then
    log "ALL 10 CHECKS PASSED"; exit 0
else
    log "FAILED: $FAIL/10"; exit 1
fi
