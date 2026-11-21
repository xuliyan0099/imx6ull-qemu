from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()

# remove MIX debug print
s = s.replace('''        fprintf(stderr, "USDHC MIX_CTRL val=%08x size=%u\\n", value, size);
''', '')

old = '''        if (size == 4) {
            s->trnmod = value & 0xffff;
            s->cmdreg = value >> 16;
'''
new = '''        if (size == 4) {
            /*
             * U-Boot places DMA enable in MIX_CTRL (bits 0 and 4) and
             * leaves the low 16 bits of CMD_XFR_TYP at zero.  Do not
             * overwrite the transfer mode already set by MIX_CTRL.
             */
            if (value & 0xffff) {
                s->trnmod = value & 0xffff;
            }
            s->cmdreg = value >> 16;
'''
if old not in s:
    raise SystemExit("4-byte block missing")
p.write_text(s.replace(old, new, 1))
print("preserve MIX_CTRL transfer mode")
