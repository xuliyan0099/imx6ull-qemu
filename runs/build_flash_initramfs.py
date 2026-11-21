import os, shutil, subprocess
root = '/tmp/initramfs-flash'
if os.path.exists(root):
    shutil.rmtree(root)
shutil.copytree('/tmp/initramfs', root, symlinks=True)
shutil.copy2('/mnt/d/Workspace/FreeRTOS/IMX6ULL/build-qemu/FreeRTOSIMX6ULL.bin', os.path.join(root,'fw.bin'))
for name in ['md5sum','dd','sync','cmp','poweroff','sleep']:
    p = os.path.join(root,'bin',name)
    if not os.path.lexists(p):
        os.symlink('/bin/busybox', p)
init = '''#!/bin/sh
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mount -t proc proc /proc
mount -t sysfs sysfs /sys
echo "=== FreeRTOS eMMC flash test ==="
i=0
while [ ! -b /dev/mmcblk1 ] && [ $i -lt 60 ]; do
  sleep 1
  i=$((i+1))
done
DEV=""
for d in /dev/mmcblk1 /dev/mmcblk0; do
  if [ -b "$d" ]; then DEV="$d"; break; fi
done
if [ -z "$DEV" ]; then echo "no mmc block device"; exec /bin/sh; fi
echo "target=$DEV size=$(wc -c < /fw.bin) bytes"
md5sum /fw.bin
dd if=/fw.bin of=$DEV bs=512 seek=2 conv=fsync
sync
dd if=$DEV of=/tmp/readback.bin bs=512 skip=2 count=32
md5sum /tmp/readback.bin
echo "=== flash done ==="
poweroff -f
'''
with open(os.path.join(root,'init'),'w') as f:
    f.write(init)
os.chmod(os.path.join(root,'init'),0o755)
cmd = "find . -print0 | cpio --null -o --format=newc --owner=0:0 2>/dev/null | gzip -9 > /tmp/flash-initramfs.cpio.gz"
subprocess.run(cmd, shell=True, cwd=root, check=True)
print('size', os.path.getsize('/tmp/flash-initramfs.cpio.gz'))
