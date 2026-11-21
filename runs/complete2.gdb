set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x808290f8
continue
printf "hit pc=%p lr=%p r0=%p\n", $pc,$lr,$r0
x/4wx 0x80ba7a28
