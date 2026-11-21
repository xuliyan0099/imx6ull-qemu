set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x8001f4e0
continue
x/64wx $sp
info registers r0 r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 sp lr pc
