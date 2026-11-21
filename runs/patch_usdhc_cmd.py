from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()
old = '''    case SDHC_TRNMOD:
        /*
         * Similar to above, but this time a write to "Command
         * Register" will be translated into a 4-byte write to
         * "Transfer Mode register" where lower 16-bit of value would
         * be set to zero. So what we do is fill those bits with
         * cached value from s->trnmod and let the SDHCI
         * infrastructure handle the rest
         */
        sdhci_write(opaque, offset, val | s->trnmod, size);
        break;
'''
new = '''    case SDHC_TRNMOD:
        /*
         * i.MX uSDHC exposes CMD_XFR_TYP as one 32-bit register: the low
         * 16 bits are the transfer mode and the high 16 bits are the
         * command index/flags.  U-Boot's FSL eSDHC driver writes it with
         * a single 32-bit store, while the generic SDHCI code only
         * starts a command on a write to the upper command byte.
         */
        if (size == 4) {
            s->trnmod = value & 0xffff;
            s->cmdreg = value >> 16;
            if (sdhci_can_issue_command(s)) {
                sdhci_send_command(s);
            }
            break;
        }
        sdhci_write(opaque, offset, val | s->trnmod, size);
        break;
'''
if old not in s:
    raise SystemExit("TRNMOD block not found")
p.write_text(s.replace(old, new, 1))
print("usdhc 32-bit CMD_XFR_TYP trigger added")
