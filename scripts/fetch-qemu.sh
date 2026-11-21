#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST=${1:-"$ROOT/../qemu-src/qemu-11.1.0.tar.xz"}
URL=${QEMU_URL:-https://download.qemu.org/qemu-11.1.0.tar.xz}
SHA256=6EE1D1A61F68212476B27108C26DA5F449DC09B626D42F8279BA0DC2E08FA858

mkdir -p "$(dirname "$DEST")"
if [ -f "$DEST" ]; then
    echo "already exists: $DEST"
else
    echo "download: $URL"
    curl -fL --retry 3 -o "$DEST.partial" "$URL"
    mv "$DEST.partial" "$DEST"
fi

actual=$(sha256sum "$DEST" | awk '{print toupper($1)}')
if [ "$actual" != "$SHA256" ]; then
    echo "SHA256 mismatch: $DEST" >&2
    echo "expected: $SHA256" >&2
    echo "actual:   $actual" >&2
    exit 1
fi
echo "ok: $DEST"
