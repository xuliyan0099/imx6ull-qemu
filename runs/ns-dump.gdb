set pagination off
set confirm off
target remote :1234
dump binary memory D:/Workspace/StudyNote/IM6/qemu/runs/guest-nosmp.bin 0x80000000 0x82000000
detach
quit
