#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="${IM6_GRAPHICS_BUILD:-/tmp/im6-graphics-rebuild}"
if [ -e "$work/qemu-11.1.0" ]; then
  echo "构建目录已存在：$work/qemu-11.1.0；请设置新的 IM6_GRAPHICS_BUILD。" >&2
  exit 1
fi
mkdir -p "$work"
tar -xJf "$root/../qemu-src/qemu-11.1.0.tar.xz" -C "$work"
cd "$work/qemu-11.1.0"
patch -p1 < "$root/experiments/graphics/qemu-graphics.patch"
patch -p1 < "$root/patches/0002-imx-gpt.patch"
patch -p1 < "$root/patches/0007-usdhc-uboot-compat.patch"
patch -p1 < "$root/patches/0009-sdhci-dma-boundary.patch"
mkdir build
cd build
../configure --target-list=arm-softmmu --disable-werror --enable-gtk --enable-slirp --disable-docs
ninja -j "${IM6_JOBS:-4}" qemu-system-arm
cp qemu-system-arm "$root/bin/qemu-system-arm-graphics-linux"
echo "built $root/bin/qemu-system-arm-graphics-linux"
