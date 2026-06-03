#!/usr/bin/env bash
# autofix_machine_items.sh — Gate 4 FIX_LOOP 的自动修复机器项
# Usage: autofix_machine_items.sh <release_dir>
# 仅尝试自动修复 pre_delivery_check.sh 机器项的失败; 对成功率 70-80%

set -eo pipefail

REL="$1"
[ -z "$REL" ] && { echo "Usage: $0 <release_dir>" >&2; exit 2; }
cd "$REL"

log() { echo "[autofix] $*"; }

# Fix 1: MANIFEST.md5 重新生成
log "重建 MANIFEST.md5"
find . -type f ! -name 'MANIFEST.*' | sort | xargs md5sum > /tmp/md5.body
{
    echo "# MANIFEST.md5 — 本文件不含自身"
    echo "# Regenerated: $(date +%F\ %T) (by autofix)"
    echo "#"
    cat /tmp/md5.body
} > MANIFEST.md5

# Fix 2: MANIFEST.sha256 重新生成
log "重建 MANIFEST.sha256"
find . -type f ! -name 'MANIFEST.*' | sort | xargs sha256sum > /tmp/sha.body
{
    echo "# MANIFEST.sha256 — 本文件不含自身"
    echo "# Regenerated: $(date +%F\ %T) (by autofix)"
    echo "#"
    cat /tmp/sha.body
} > MANIFEST.sha256

# Fix 3: 硬编码路径 sed 替换（保守）
log "扫描并替换内部路径"
while IFS= read -r f; do
    [ -f "$f" ] || continue
    sed -i.bak 's|/home/[a-z0-9]*/\([a-zA-Z0-9_-]*\)|${BSA_ROOT}/\1|g; s|sxyH3:|remote:|g' "$f" 2>/dev/null || true
    rm -f "$f.bak"
done < <(find . -maxdepth 2 \( -name '*.md' -o -name '*.sh' -o -name '*.py' -o -name '*.R' -o -name '*.yml' -o -name '*.yaml' \) 2>/dev/null)

# Fix 4: 生成缺失 PNG (若 PDF 存在)
log "补齐 PDF → PNG"
if command -v pdftoppm > /dev/null; then
    for pdf in figures/*.pdf; do
        [ -f "$pdf" ] || continue
        png="${pdf%.pdf}.png"
        if [ ! -f "$png" ]; then
            pdftoppm -png -r 600 "$pdf" "${png%.png}" 2>/dev/null || true
            [ -f "${png%.png}-1.png" ] && mv "${png%.png}-1.png" "$png"
        fi
    done
fi

# Fix 5: 确保 VERSION 存在
[ -f VERSION ] || echo "v2.1-draft" > VERSION

log "autofix 完成, 重新跑 pre_delivery_check.sh"
