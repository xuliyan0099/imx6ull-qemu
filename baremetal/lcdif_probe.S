@ Minimal i.MX6ULL eLCDIF probe for QEMU mcimx6ul-evk.
@ Draws 800x480 color bars straight into DDR and programs LCDIF.
.syntax unified
.arm
.section .text
.global _start
_start:
    ldr   r0, =0x80100000        @ framebuffer (physical DDR)
    ldr   r11, =800
    mov   r4, #0                 @ y
row_loop:
    mov   r5, #0                 @ x
col_loop:
    lsr   r6, r5, #7             @ bar index 0..6
    adr   r7, colors
    ldr   r8, [r7, r6, lsl #2]
    mul   r10, r4, r11
    add   r10, r10, r5
    str   r8, [r0, r10, lsl #2]
    add   r5, r5, #1
    cmp   r5, r11
    blt   col_loop
    add   r4, r4, #1
    cmp   r4, #480
    blt   row_loop

    ldr   r1, =0x021C8000        @ LCDIF base
    ldr   r2, =(480 << 16) | 800
    str   r2, [r1, #0x30]        @ V4_TRANSFER_COUNT
    ldr   r2, =0x80100000
    str   r2, [r1, #0x40]        @ V4_CUR_BUF
    str   r2, [r1, #0x50]        @ V4_NEXT_BUF
    ldr   r2, =(3 << 10) | (3 << 8) | (1 << 5) | 1
    str   r2, [r1, #0x00]        @ CTRL: RUN + WORD_LENGTH=24bit + 24bit bus
    dsb   sy

hang:
    b     hang

.align 4
colors:
    .word 0x00FF0000
    .word 0x0000FF00
    .word 0x000000FF
    .word 0x00FFFF00
    .word 0x00FF00FF
    .word 0x0000FFFF
    .word 0x00FFFFFF
