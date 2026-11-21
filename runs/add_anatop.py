from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
anchor = '''    /*
     * AIPS bridge configuration registers.  U-Boot's init_aips() writes
'''
insert = '''    /*
     * ANATOP analog registers.  U-Boot polls ANATOP+0x150 bit 7 for PLL
     * lock before it programs the CCM; model the block as RAM and report
     * the lock bit as set.
     */
    memory_region_init_ram(&s->analog, OBJECT(dev), "imx6ul.analog",
                           FSL_IMX6UL_ANALOG_SIZE, &error_abort);
    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_ANALOG_ADDR,
                                &s->analog);
    {
        uint32_t *p = (uint32_t *)memory_region_get_ram_ptr(&s->analog);
        p[0x150 / 4] = 0x80;
    }

'''
if anchor not in s:
    raise SystemExit("AIPS anchor not found")
p.write_text(s.replace(anchor, insert + anchor, 1))

h = Path("/tmp/qemu-11.1.0/include/hw/arm/fsl-imx6ul.h")
hs = h.read_text()
oldh = '''    MemoryRegion       caam;
    MemoryRegion       mmdc;
'''
newh = '''    MemoryRegion       caam;
    MemoryRegion       mmdc;
    MemoryRegion       analog;
'''
if oldh not in hs:
    raise SystemExit("header anchor not found")
h.write_text(hs.replace(oldh, newh))
print("ANATOP lock model added")
