#!/usr/bin/env bash
set -euo pipefail
root=/mnt/d/Workspace/StudyNote/IM6/qemu
official='/mnt/d/Workspace/IM6/【正点原子】阿尔法Linux开发板（A盘）-基础资料/08、系统镜像/01、出厂系统镜像'
archive="$official/03、文件系统/rootfs.tar.bz2"
out="$root/images/official-rootfs.ext4"
if [ -e "$out" ]; then echo "目标已存在：$out" >&2; exit 1; fi
work=$(mktemp -d /tmp/im6-official-rootfs-XXXXXX)
mkdir "$work/root"
printf '使用官方根文件系统：%s\n临时目录：%s\n' "$archive" "$work"
export IM6_ROOTFS_ARCHIVE="$archive" IM6_ROOTFS_WORK="$work"
fakeroot bash -eu -c '
  tar -xjf "$IM6_ROOTFS_ARCHIVE" -C "$IM6_ROOTFS_WORK/root" --same-owner
  truncate -s 2G "$IM6_ROOTFS_WORK/rootfs.ext4"
  mkfs.ext4 -q -F -L IM6OFFICIAL -d "$IM6_ROOTFS_WORK/root" "$IM6_ROOTFS_WORK/rootfs.ext4"
'
e2fsck -fn "$work/rootfs.ext4"
cp --sparse=always "$work/rootfs.ext4" "$out.partial"
mv "$out.partial" "$out"
printf '完成：%s\n' "$out"
