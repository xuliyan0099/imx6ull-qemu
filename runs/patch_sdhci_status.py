from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/sd/sdhci.c")
s = p.read_text()

old1 = '''    if (s->norintstsen & SDHC_NISEN_CMDCMP) {
        s->norintsts |= SDHC_NIS_CMDCMP;
    }
'''
new1 = '''    /*
     * INT_STATUS is a raw status register on real SDHCI/eSDHC hardware;
     * INT_STATUS_EN only gates the interrupt line.  U-Boot polls raw
     * status with interrupts disabled, so set the bit unconditionally.
     */
    s->norintsts |= SDHC_NIS_CMDCMP;
'''
if old1 not in s:
    raise SystemExit("CMD complete block not found")
s = s.replace(old1, new1, 1)

old2 = '''    if (s->norintstsen & SDHC_NISEN_TRSCMP) {
        s->norintsts |= SDHC_NIS_TRSCMP;
    }

    sdhci_update_irq(s);
}

/*
 * Programmed i/o data transfer
 */
'''
new2 = '''    /* Raw status, independent of INT_STATUS_EN (see sdhci_send_command). */
    s->norintsts |= SDHC_NIS_TRSCMP;

    sdhci_update_irq(s);
}

/*
 * Programmed i/o data transfer
 */
'''
if old2 not in s:
    raise SystemExit("TRANSFER complete block not found")
s = s.replace(old2, new2, 1)

p.write_text(s)
print("SDHCI raw status bits made unconditional")
