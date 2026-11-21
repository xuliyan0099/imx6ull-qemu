.section .text
.global _start

_start:
    ldr r0, =0x02020000       @ UART1 base
    ldr r1, =message
1:
    ldrb r2, [r1], #1
    cmp r2, #0
    beq 2f
    str r2, [r0, #0x40]       @ UTXD
    b 1b
2:
    b 2b

.section .rodata
message:
    .asciz "Hello i.MX6ULL QEMU UART\r\n"
