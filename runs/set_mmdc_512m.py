from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c")
s = p.read_text()
anchor = '''    memory_region_init_ram(&s->mmdc, OBJECT(dev), "imx6ul.mmdc",
                           FSL_IMX6UL_MMDC_CFG_SIZE, &error_abort);
    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_MMDC_CFG_ADDR,
                                &s->mmdc);
'''
replacement = anchor + '''    {
        /*
         * Reset values matching the 512MB DDR3L configuration used by the
         * Alientek U-Boot.  imx_ddr_size() derives 512MB from MDCTL density
         * bits 20..22 and the DDR3 MDMISC type field.
         */
        uint32_t *p = (uint32_t *)memory_region_get_ram_ptr(&s->mmdc);
        p[0x00 / 4] = 0x00300000; /* MDCTL: density code -> 512MB */
        p[0x18 / 4] = 0x00201740; /* MDMISC: DDR3, 32-bit bus */
        p[0x800 / 4] = 0x00000001; /* MPZQHWCTRL: calibration done */
    }
'''
if anchor not in s:
    raise SystemExit("MMDC block not found")
p.write_text(s.replace(anchor, replacement, 1))
print("MMDC 512MB reset values set")
