set pagination off
set confirm off
target remote :1234
info registers pc lr sp cpsr
x/8i $pc
x/8wx 0x02020000
