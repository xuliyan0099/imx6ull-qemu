@echo off
setlocal
set WSLDIST=Ubuntu-24.04
set QDIR=/mnt/d/Workspace/StudyNote/IM6/qemu
wsl -d %WSLDIST% -- bash -lc "cd %QDIR% && exec ./bin/qemu-system-arm-linux -M mcimx6ull-alientek -m 512 -smp 1 -kernel images/zImage-nxp-fb -initrd initramfs/net-initramfs.cpio.gz -dtb images/board-alientek-full.dtb -append 'console=ttymxc0,115200 rdinit=/init ignore_loglevel' -drive if=sd,index=0,format=raw,file=images/tf.img -drive if=sd,index=1,format=raw,file=images/emmc.img -nic user,model=imx.enet -nic user,model=imx.enet -serial stdio -display none -no-reboot"
