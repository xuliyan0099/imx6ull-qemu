from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()

# remove debug print
s = s.replace('''        fprintf(stderr, "USDHC CMD_XFR_TYP val=%08x size=%u trnmod=%04x cmdreg=%04x\\n",
                value, size, s->trnmod, s->cmdreg);
''', '')

old = '''    case SDHC_TRNMOD:
        /*
         * i.MX uSDHC exposes CMD_XFR_TYP as one 32-bit register: the low
'''
new = '''    case SDHC_CLKCON:
        /*
         * U-Boot's FSL eSDHC driver programs the NXP SYSCTL layout
         * (SDCLKFS in bits 15:8, DVS in bits 7:4) and does not set the
         * SDHCI internal-clock-enable bits.  Translate it into the
         * SDHCI clock state expected by the generic model.
         */
        s->clkcon = (value & 0xffff) |
                    SDHC_CLOCK_INT_EN | SDHC_CLOCK_INT_STABLE |
                    SDHC_CLOCK_SDCLK_EN;
        s->timeoutcon = value >> 16;
        break;

    case SDHC_TRNMOD:
        /*
         * i.MX uSDHC exposes CMD_XFR_TYP as one 32-bit register: the low
'''
if old not in s:
    raise SystemExit("TRNMOD marker missing")
p.write_text(s.replace(old, new, 1))
print("eSDHC SYSCTL clock translation added")
