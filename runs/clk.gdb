set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x8001f4e0
continue
printf "clk base ptrs:\n"
x/8wx 0x80c44bd0+189*4
x/8wx 0x80c44bd0+185*4
x/4wx 0x80c44bd0+217*4
