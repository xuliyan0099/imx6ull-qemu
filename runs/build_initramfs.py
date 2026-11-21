import os, shutil, subprocess, stat
root = '/tmp/initramfs'
if os.path.exists(root):
    shutil.rmtree(root)
for d in ['bin','sbin','etc','dev','proc','sys','tmp','root','lib','usr/bin','usr/sbin']:
    os.makedirs(os.path.join(root,d), exist_ok=True)

src_root = '/tmp/imx6ull-rootfs'
shutil.copy2(os.path.join(src_root,'bin/busybox.nosuid'), os.path.join(root,'bin/busybox'))
os.chmod(os.path.join(root,'bin/busybox'), 0o755)
for lib in ['ld-2.23.so','libc-2.23.so','libm-2.23.so']:
    shutil.copy2(os.path.join(src_root,'lib',lib), os.path.join(root,'lib',lib))
os.symlink('ld-2.23.so', os.path.join(root,'lib/ld-linux-armhf.so.3'))
os.symlink('libc-2.23.so', os.path.join(root,'lib/libc.so.6'))
os.symlink('libm-2.23.so', os.path.join(root,'lib/libm.so.6'))

for name in ['sh','mount','umount','ls','cat','echo','dmesg','ifconfig','ip','mdev',
             'poweroff','reboot','uname','free','ps','df','sleep','vi','mkdir','rm',
             'cp','mv','ln','chmod','grep','find','tar','gzip','head','tail','wc',
             'kill','top','route','ping','udhcpc','insmod','lsmod','sed',
             'md5sum','dd','sync','cmp','poweroff']:
    if not os.path.lexists(os.path.join(root,'bin',name)):
        os.symlink('/bin/busybox', os.path.join(root,'bin',name))

init = '''#!/bin/sh
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mkdir -p /dev/pts
mount -t devpts devpts /dev/pts 2>/dev/null
echo
echo "=== IMX6ULL QEMU initramfs shell ==="
echo "Kernel: $(uname -a)"
echo "Cmdline: $(cat /proc/cmdline)"
echo "Memory: $(free | sed -n 2p)"
echo "MMC: $(cat /proc/partitions | grep mmc || echo none)"
echo
exec /bin/sh
'''
with open(os.path.join(root,'init'),'w') as f:
    f.write(init)
os.chmod(os.path.join(root,'init'),0o755)

# cpio newc with root ownership
cmd = "find . -print0 | cpio --null -o --format=newc --owner=0:0 2>/dev/null | gzip -9 > /tmp/initramfs.cpio.gz"
r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
print('rc', r.returncode, r.stderr[-200:])
print('size', os.path.getsize('/tmp/initramfs.cpio.gz'))
