from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
old = '''    /*
     * MMDC
     */
    create_unimplemented_device("a7mpcore-mmdc", FSL_IMX6UL_MMDC_CFG_ADDR,
                                FSL_IMX6UL_MMDC_CFG_SIZE);
'''
new = '''    /*
     * MMDC: model the register window as writable RAM.  The real DDR
     * training sequence is not required because QEMU already maps RAM at
     * the MMDC address; the status/control registers must not abort or
     * return an unassigned-device value when U-Boot/Linux probe them.
     */
    memory_region_init_ram(&s->mmdc, OBJECT(dev), "imx6ul.mmdc",
                           FSL_IMX6UL_MMDC_CFG_SIZE, &error_abort);
    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_MMDC_CFG_ADDR,
                                &s->mmdc);
'''
if old not in s:
    raise SystemExit("MMDC block not found")
p.write_text(s.replace(old, new))

h = Path("/tmp/qemu-11.1.0/include/hw/arm/fsl-imx6ul.h")
hs = h.read_text()
oldh = '''    MemoryRegion       caam;
    MemoryRegion       iomuxc;
'''
newh = '''    MemoryRegion       caam;
    MemoryRegion       mmdc;
    MemoryRegion       iomuxc;
'''
if oldh not in hs:
    raise SystemExit("header block not found")
h.write_text(hs.replace(oldh, newh))
print("MMDC RAM model added")
