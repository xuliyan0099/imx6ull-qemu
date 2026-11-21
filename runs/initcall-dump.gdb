set pagination off
set confirm off
target remote :1234
dump binary memory D:/Workspace/StudyNote/IM6/qemu/runs/guest-initcall.bin 0x80000000 0xa0000000
detach
quit
