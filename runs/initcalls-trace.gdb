set pagination off
set confirm off
target remote :1234
set {int}0x020c4038 = 0x00029148
b *0x8004e790
commands
silent
printf "CALL %p\n", $r0
continue
end
continue
