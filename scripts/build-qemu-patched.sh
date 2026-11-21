#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/d/Workspace/StudyNote/IM6/qemu
SRC_TAR="$ROOT/../qemu-src/qemu-11.1.0.tar.xz"
BUILD=${BUILD:-/tmp/qemu-11.1.0-build}

mkdir -p "$BUILD"
if [ ! -d "$BUILD/qemu-11.1.0" ]; then
  tar -xJf "$SRC_TAR" -C "$BUILD"
fi

cd "$BUILD/qemu-11.1.0"
for p in "$ROOT"/patches/000*.patch; do
  patch -p1 --forward < "$p"
done

if [ ! -d build ]; then
  mkdir build
fi
cd build
../configure \
  --target-list=arm-softmmu \
  --disable-werror \
  --enable-gtk \
  --enable-slirp \
  --disable-docs
ninja qemu-system-arm -j"$(nproc)"
cp qemu-system-arm "$ROOT/bin/qemu-system-arm-linux"
echo "built: $ROOT/bin/qemu-system-arm-linux"
