from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
anchor = '''    /*
     * OCOTP
     */
'''
insert = '''    /*
     * i.MX6ULL U-Boot/MX6 get_cpu_rev() probes 0x00a00004.  The real SoC
     * decodes this as a ROM/BootROM auxiliary window; QEMU needs a
     * non-aborting mapping so the early boot code can continue.
     */
    create_unimplemented_device("imx6ull-aux", 0x00a00000, 0x1000);

'''
if anchor not in s:
    raise SystemExit("anchor not found")
p.write_text(s.replace(anchor, insert + anchor, 1))
print("aux window added")
