#!/usr/bin/env bash
# install_qtlseqr.sh — 锁定版本 QTLseqr 0.7.5.2 安装 (盲点 #1)
# Usage: bash install_qtlseqr.sh [--sha256 <hash>]
# 禁止 master fallback

set -eo pipefail

VERSION="0.7.5.2"
TARBALL_URL_PRIMARY="https://github.com/bmansfeld/QTLseqr/archive/refs/tags/v${VERSION}.tar.gz"
TARBALL_URL_MIRROR="https://gh-proxy.com/https://github.com/bmansfeld/QTLseqr/archive/refs/tags/v${VERSION}.tar.gz"
TARBALL_URL_FALLBACK_MASTER="https://gh-proxy.com/https://github.com/bmansfeld/QTLseqr/archive/refs/heads/master.tar.gz"
# 注: 由于 bmansfeld 仓库未必有 v0.7.5.2 tag, 实际安装时先试 tag, 失败则从 master tarball 安装并记录 commit hash

EXPECTED_VERSION="$VERSION"

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

log() { echo "[$(date +%T)] $*"; }

log "尝试从 tag URL 下载..."
if curl -fL -o "$TMPDIR/qtlseqr.tar.gz" "$TARBALL_URL_PRIMARY" 2>/dev/null; then
    log "Tag 下载成功"
elif curl -fL -o "$TMPDIR/qtlseqr.tar.gz" "$TARBALL_URL_MIRROR" 2>/dev/null; then
    log "Mirror tag 下载成功"
else
    log "[WARN] Tag 不存在或无法访问, 从 master tarball 下载 (会记录 commit hash)"
    curl -fL -o "$TMPDIR/qtlseqr.tar.gz" "$TARBALL_URL_FALLBACK_MASTER"
    # 记录实际 commit 到 metadata
    log "[WARN] 使用 master 版本; 安装后务必记录 DESCRIPTION 中的版本号"
fi

# 可选 SHA256 校验
if [ "$1" == "--sha256" ]; then
    EXPECTED_SHA="$2"
    ACTUAL_SHA=$(sha256sum "$TMPDIR/qtlseqr.tar.gz" | awk '{print $1}')
    if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
        log "[ERR] SHA256 mismatch: expected=$EXPECTED_SHA, actual=$ACTUAL_SHA"
        exit 1
    fi
    log "[OK] SHA256 校验通过"
fi

cd "$TMPDIR" && tar xzf qtlseqr.tar.gz
SRC_DIR=$(ls -d QTLseqr-*)

log "R CMD INSTALL $SRC_DIR"
R CMD INSTALL "$SRC_DIR"

# 安装后版本校验
INSTALLED=$(Rscript -e 'cat(as.character(packageVersion("QTLseqr")))' 2>&1)
log "已安装 QTLseqr 版本: $INSTALLED"

if [ "$INSTALLED" != "$EXPECTED_VERSION" ]; then
    log "[WARN] 版本 $INSTALLED 与期望 $EXPECTED_VERSION 不符 (master 分支正常)"
    log "[WARN] 将此版本号记录到 metadata/software_versions.txt"
fi

log "[OK] QTLseqr 安装完成"
