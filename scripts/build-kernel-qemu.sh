#!/usr/bin/env bash
set -euo pipefail

ROOT=/mnt/d/Workspace/StudyNote/IM6/qemu
KSRC=${KSRC:-/tmp/linux-imx}
PATCH="$ROOT/patches/linux-imx-4.1.15-qemu.patch"
CROSS=${CROSS:-arm-none-eabi-}
JOBS=${JOBS:-$(nproc)}

if [ ! -d "$KSRC/.git" ]; then
  git clone --depth 1 --branch rel_imx_4.1.15_2.1.0_ga \
    https://github.com/nxp-imx/linux-imx.git "$KSRC"
fi

cd "$KSRC"
git checkout -- .
git apply "$PATCH"

make ARCH=arm CROSS_COMPILE="${CROSS}" imx_v7_defconfig
scripts/config --disable MXC_GPU_VIV
scripts/config --disable KERNEL_LZO
scripts/config --disable KERNEL_LZ4
scripts/config --enable KERNEL_GZIP

make ARCH=arm CROSS_COMPILE="${CROSS}" HOSTCFLAGS=-fcommon -j"$JOBS" zImage
cp arch/arm/boot/zImage "$ROOT/images/zImage-nxp-fb"
echo "built: $ROOT/images/zImage-nxp-fb"
