set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x8001f4e0
continue
printf "hit pc=%p lr=%p sp=%p\n", $pc, $lr, $sp
bt
x/16i $pc
