set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x80b4cc8c
b *0x80b4ccf4
b *0x80b4cd30
continue
printf "hit pc=%p lr=%p r0=%p\n", $pc,$lr,$r0
