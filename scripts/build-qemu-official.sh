#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
work="${IM6_OFFICIAL_BUILD:-/tmp/im6-official-qemu}"
if [ -e "$work/qemu-11.1.0" ]; then
  echo "构建目录已存在，请设置新的 IM6_OFFICIAL_BUILD。" >&2
  exit 1
fi
mkdir -p "$work"
tar -xJf "$root/../qemu-src/qemu-11.1.0.tar.xz" -C "$work"
cd "$work/qemu-11.1.0"
patch -p1 < "$root/experiments/graphics/qemu-graphics.patch"
patch -p1 < "$root/patches/0002-imx-gpt.patch"
patch -p1 < "$root/patches/0007-usdhc-uboot-compat.patch"
patch -p1 < "$root/patches/0009-sdhci-dma-boundary.patch"
cp "$root/src/im6-goodix-linux.c" hw/arm/im6-gt1158.c
python3 - <<'PY'
from pathlib import Path
path = Path('hw/arm/mcimx6ull-alientek.c')
source = path.read_text()
old = '    i2c_slave_create_simple(s->i2c[1].bus, "im6-gt1158", 0x14);'
new = '''    I2CSlave *touch = i2c_slave_create_simple(s->i2c[1].bus,
                                               "im6-goodix-linux", 0x5d);
    qdev_connect_gpio_out(DEVICE(touch), 0,
                          qdev_get_gpio_in(DEVICE(&s->gpio[0]), 9));'''
if source.count(old) != 1:
    raise RuntimeError('找不到唯一的触摸接线位置')
path.write_text(source.replace(old, new))
PY
if [ "${IM6_AUDIO:-1}" != "0" ]; then
  python3 "$root/scripts/patch-qemu-audio.py" .
fi
alsa_flag=""
if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists alsa; then
  alsa_flag="--enable-alsa"
fi
mkdir build
cd build
../configure --target-list=arm-softmmu --disable-werror --enable-gtk --enable-slirp \
  ${alsa_flag} --disable-docs
ninja -j "${IM6_JOBS:-4}" qemu-system-arm
cp qemu-system-arm "$root/bin/qemu-system-arm-official-linux.partial"
mv "$root/bin/qemu-system-arm-official-linux.partial" "$root/bin/qemu-system-arm-official-linux"
cp "$root/images/board-alientek-full.dtb" "$root/images/board-alientek-official-gui.dtb"
fdtput -t i "$root/images/board-alientek-official-gui.dtb" \
  /soc/aips-bus@02100000/lcdif@021c8000/display bits-per-pixel 32
echo "built $root/bin/qemu-system-arm-official-linux"
