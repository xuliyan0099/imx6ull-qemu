set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x80821268
continue
printf "hit pc=%p lr=%p\n", $pc,$lr
info registers r0 r1 r2 r3 r4
