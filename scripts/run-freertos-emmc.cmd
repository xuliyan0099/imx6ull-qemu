@echo off
wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/d/Workspace/StudyNote/IM6/qemu && exec ./bin/qemu-system-arm-linux -M mcimx6ull-alientek -m 512 -smp 1 -watchdog-action none -drive if=sd,index=0,format=raw,file=images/tf.img -drive if=sd,index=1,format=raw,file=images/emmc-uboot-freertos.img -display none -monitor none -serial stdio -no-reboot"
