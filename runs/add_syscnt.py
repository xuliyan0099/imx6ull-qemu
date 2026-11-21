from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
anchor = '''    /*
     * AIPS bridge configuration registers.  U-Boot's init_aips() writes
'''
insert = '''    /*
     * A7 MPCore system counter/compare/control window.  U-Boot's
     * timer_init() programs the global timer control register here.
     */
    create_unimplemented_device("a7mpcore-syscnt", 0x021d4000, 0xc000);

'''
if anchor not in s:
    raise SystemExit("anchor not found")
p.write_text(s.replace(anchor, insert + anchor, 1))
print("system counter window added")
