#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TARGET="$ROOT/web/deps"

mkdir -p "$TARGET"
python3 -m pip install --upgrade --target "$TARGET" -r "$ROOT/web/requirements.txt"
echo "web dependencies installed: $TARGET"
