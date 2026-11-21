set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x80b69bec
continue
continue
