#!/bin/bash
cd /mnt/d/Workspace/StudyNote/IM6/qemu || exit 1
{
  sleep 9
  echo 'echo 20e0000.iomuxc > /sys/bus/platform/drivers/imx6ul-pinctrl/bind'
  sleep 3
  echo 'dmesg | grep -i "mxsfb\|pinctrl\|fb0" | tail -10'
  echo 'ls -l /dev/fb0 /dev/fb1 2>/dev/null'
  echo 'cat /sys/class/graphics/fb0/modes 2>/dev/null'
  sleep 1
  echo 'echo BOUND_END'
  sleep 2
} | timeout 25 ./bin/qemu-system-arm-linux \
  -M mcimx6ul-evk -m 512 -smp 1 \
  -kernel images/zImage -initrd initramfs/initramfs.cpio.gz \
  -dtb images/board-lcd-pinctrl.dtb \
  -append 'console=ttymxc0,115200 rdinit=/init ignore_loglevel initcall_blacklist=imx6ul_pinctrl_init' \
  -serial stdio -display none -no-reboot > runs/manual-bind.log 2>&1
echo rc=$?
tail -50 runs/manual-bind.log
