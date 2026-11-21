@echo off
setlocal
set WSLDIST=Ubuntu-24.04
set QDIR=/mnt/d/Workspace/StudyNote/IM6/qemu
wsl -d %WSLDIST% -- bash -lc "cd %QDIR% && exec ./bin/qemu-system-arm-linux -M mcimx6ull-alientek -m 512 -smp 1 -kernel /mnt/d/Workspace/FreeRTOS/IMX6ULL/build-qemu/FreeRTOSIMX6ULL.elf -serial stdio -display none -no-reboot"
