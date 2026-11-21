#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dest="${IM6_IMAGE_DIR:-/opt/im6/images}"

sudo mkdir -p "$dest"
sudo chown "$(id -u):$(id -g)" "$dest"

# The factory rootfs is the only large image read heavily at boot.
names=(official-rootfs.ext4 zImage board-alientek-full.dtb board-alientek-official-gui.dtb ramdisk.uimg tf.img)

for name in "${names[@]}"; do
  src="$root/images/$name"
  dst="$dest/$name"
  if [ ! -f "$src" ]; then
    echo "缺少 $src，跳过" >&2
    continue
  fi
  if [ -f "$dst" ] && [ "$(stat -c%s "$src")" = "$(stat -c%s "$dst")" ]; then
    echo "已存在 $dst"
    continue
  fi
  echo "复制 $name 到 $dst"
  cp --sparse=always "$src" "$dst.partial"
  mv "$dst.partial" "$dst"
done

if [ "${IM6_COPY_EMMC:-0}" = 1 ]; then
  for name in uboot-emmc.img emmc-uboot-freertos.img; do
    src="$root/images/$name"
    dst="$dest/$name"
    if [ -f "$dst" ] && [ "$(stat -c%s "$src")" = "$(stat -c%s "$dst")" ]; then
      echo "已存在 $dst"
      continue
    fi
    echo "复制 $name 到 $dst（8GB）"
    cp --sparse=always "$src" "$dst.partial"
    mv "$dst.partial" "$dst"
  done
fi

sync
echo "镜像目录: $dest"
du -sh "$dest"
