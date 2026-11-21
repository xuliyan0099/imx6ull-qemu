from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()
old = '''    case SDHC_TRNMOD:
        /*
         * i.MX uSDHC exposes CMD_XFR_TYP as one 32-bit register: the low
'''
new = '''    case SDHC_TRNMOD:
        fprintf(stderr, "USDHC CMD_XFR_TYP val=%08x size=%u trnmod=%04x cmdreg=%04x\\n",
                value, size, s->trnmod, s->cmdreg);
        /*
         * i.MX uSDHC exposes CMD_XFR_TYP as one 32-bit register: the low
'''
if old not in s:
    raise SystemExit("TRNMOD marker missing")
p.write_text(s.replace(old, new, 1))
print("debug log added")
