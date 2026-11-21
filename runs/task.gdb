set pagination off
set confirm off
target remote :1234
x/8wx 0x80bd0000
x/8wx 0x80c43280
x/8wx 0x80c43280+0x8c
x/4wx 0x80c43280+0x5c
