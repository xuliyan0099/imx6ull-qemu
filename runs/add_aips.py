from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
anchor = '''    /*
     * i.MX6ULL U-Boot/MX6 get_cpu_rev() probes 0x00a00004.  The real SoC
     * decodes this as a ROM/BootROM auxiliary window; QEMU needs a
     * non-aborting mapping so the early boot code can continue.
     */
    create_unimplemented_device("imx6ull-aux", 0x00a00000, 0x1000);
'''
insert = anchor + '''
    /*
     * AIPS bridge configuration registers.  U-Boot's init_aips() writes
     * the access-control registers before it uses any peripherals; the
     * writes must not cause an external abort.
     */
    create_unimplemented_device("aips1", FSL_IMX6UL_AIPS1_CFG_ADDR,
                                FSL_IMX6UL_AIPS1_CFG_SIZE);
    create_unimplemented_device("aips2", FSL_IMX6UL_AIPS2_CFG_ADDR,
                                FSL_IMX6UL_AIPS2_CFG_SIZE);
    create_unimplemented_device("aips3", 0x0227c000, 0x1000);
'''
if anchor not in s:
    raise SystemExit("anchor not found")
p.write_text(s.replace(anchor, insert, 1))
print("AIPS mappings added")
