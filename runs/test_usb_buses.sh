#!/bin/bash
Q=/tmp/im6-official-audio/build/qemu-system-arm
P=/mnt/d/Workspace/StudyNote/IM6/qemu
for b in usb-bus.1 usb-bus.0; do
  echo "===$b==="
  timeout 15 "$Q" \
   -M mcimx6ull-alientek -m 512 -smp 1 \
   -drive if=sd,index=0,format=raw,file="$P/images/official-rootfs.ext4",cache=unsafe \
   -drive if=sd,index=1,format=raw,file="$P/images/uboot-emmc.img",cache=unsafe \
   -device loader,file="$P/images/zImage",addr=0x80800000,force-raw=on \
   -device loader,file="$P/images/board-alientek-official-gui.dtb",addr=0x83000000,force-raw=on \
   -nic user,model=imx.enet -nic user,model=imx.enet \
   -audiodev none,id=im6snd -device usb-audio,bus="$b",audiodev=im6snd \
   -serial stdio -display none -no-reboot 2>&1 | head -6
  echo "rc=${PIPESTATUS[0]}"
done
