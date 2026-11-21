set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
continue &
python import time; time.sleep(12)
interrupt
info registers pc lr sp cpsr
x/12i $pc
bt
