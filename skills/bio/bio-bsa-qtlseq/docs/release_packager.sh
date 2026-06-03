#!/usr/bin/env bash
# release_packager.sh — 打包 release v2.x + MD5 + SHA256
# Usage: release_packager.sh <project_dir> <release_version>
# 输入: project_dir (含 analysis_v2/ 等)
# 输出: release/ + release_<project_id>_<version>-draft.tar.gz

set -eo pipefail

PROJECT_DIR="$1"
VERSION="${2:-v2.1}"
if [ -z "$PROJECT_DIR" ]; then
    echo "Usage: $0 <project_dir> [version]" >&2; exit 2
fi

cd "$PROJECT_DIR"
REL_DIR="release"
rm -rf "$REL_DIR"
mkdir -p "$REL_DIR"/{results/{main,sensitivity/{window_500kb,refAF_035}},figures,scripts,metadata}

SKILL_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"

# 1. 从 analysis_v2 拷贝 results/figures/scripts (小文件优先, 排除大 rds/all_snps)
log() { echo "[$(date +%T)] $*"; }
log "1/6 复制结果文件"
rsync -av --exclude='*all_snps*' --exclude='*.rds' --exclude='genes.bed' \
    analysis/results_v2/ "$REL_DIR/results/_tmp/" 2>/dev/null || true

# 按文件名分类到 main/ sensitivity/
cd "$REL_DIR/results/_tmp" 2>/dev/null || { log "[WARN] results_v2 未找到"; cd "$PROJECT_DIR"; }
if [ -d "$REL_DIR/results/_tmp" ]; then
    cd "$PROJECT_DIR"
    for f in "$REL_DIR/results/_tmp"/*; do
        [ -f "$f" ] || continue
        name=$(basename "$f")
        if [[ "$name" == *_w500k* ]]; then
            mv "$f" "$REL_DIR/results/sensitivity/window_500kb/"
        elif [[ "$name" == *_rf035* ]]; then
            mv "$f" "$REL_DIR/results/sensitivity/refAF_035/"
        else
            mv "$f" "$REL_DIR/results/main/"
        fi
    done
    rmdir "$REL_DIR/results/_tmp"
fi

# 2. 复制 figures + scripts + metadata
log "2/6 复制 figures/scripts/metadata"
rsync -av analysis/figures_v2/ "$REL_DIR/figures/" 2>/dev/null || true
cp analysis/scripts/*_v2.* "$REL_DIR/scripts/" 2>/dev/null || true
cp metadata/* "$REL_DIR/metadata/" 2>/dev/null || true

# 3. 生成 PNG (Codex R2-B3)
log "3/6 PDF → PNG (600 dpi)"
for pdf in "$REL_DIR/figures"/*.pdf; do
    [ -f "$pdf" ] || continue
    png="${pdf%.pdf}.png"
    if command -v pdftoppm > /dev/null; then
        pdftoppm -png -r 600 "$pdf" "${png%.png}" 2>/dev/null || log "[WARN] pdftoppm 失败: $pdf"
        # pdftoppm 会加 -1 后缀, 重命名
        [ -f "${png%.png}-1.png" ] && mv "${png%.png}-1.png" "$png"
    elif command -v convert > /dev/null; then
        convert -density 600 "$pdf" "$png" 2>/dev/null || log "[WARN] convert 失败"
    else
        log "[WARN] 无 pdftoppm/convert, 跳过 PNG 生成"
    fi
done

# 4. 渲染 MD 模板（简化：直接复制, 占位符手工替换）
log "4/6 渲染 MD 模板"
for tpl in 00_README 01_METHODS 02_LIMITATIONS 03_COLUMN_DEFINITIONS HOWTO_GO_KEGG CHANGELOG Top_QTL_annotated; do
    cp "$SKILL_ROOT/docs/${tpl}.md.template" "$REL_DIR/${tpl}.md" 2>/dev/null || true
done
cp "$SKILL_ROOT/docs/figures_README.md.template" "$REL_DIR/figures/README.md" 2>/dev/null || true

# 5. VERSION + 目录 README
log "5/6 VERSION / 目录 README"
cat > "$REL_DIR/VERSION" <<EOF
${VERSION}
release_date: $(date +%F)
project_id: $(basename "$PROJECT_DIR")
EOF

cat > "$REL_DIR/results/sensitivity/window_500kb/README.md" <<EOF
# 敏感性分析: window=500kb
目的: 验证主候选稳健性 + 诊断染色体级峰真伪
详见: ../../../02_LIMITATIONS.md §3.5
EOF

cat > "$REL_DIR/results/sensitivity/refAF_035/README.md" <<EOF
# 敏感性分析: refAlleleFreq=0.35
目的: 与 QTLseqr vignette 默认值对照，验证主候选在更严格 AF 过滤下稳健性
详见: ../../../02_LIMITATIONS.md §3.5
EOF

# 6. MD5 + SHA256 manifest
log "6/6 MANIFEST.md5 + MANIFEST.sha256"
cd "$REL_DIR"
find . -type f ! -name 'MANIFEST.*' | sort | xargs md5sum > /tmp/md5.body
{
    echo "# MANIFEST.md5 — 本文件不含自身"
    echo "# Generated: $(date +%F\ %T)"
    echo "# Version: ${VERSION}"
    echo "#"
    cat /tmp/md5.body
} > MANIFEST.md5

find . -type f ! -name 'MANIFEST.*' | sort | xargs sha256sum > /tmp/sha256.body
{
    echo "# MANIFEST.sha256 — 本文件不含自身"
    echo "# Generated: $(date +%F\ %T)"
    echo "#"
    cat /tmp/sha256.body
} > MANIFEST.sha256

cd ..
log "[OK] release/ 目录就绪"
log "  文件数: $(find "$REL_DIR" -type f | wc -l)"
log "  大小: $(du -sh "$REL_DIR" | awk '{print $1}')"
log "  下一步: 跑 pre_delivery_check.sh + project-audit"
