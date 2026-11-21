import re
hdr = '/tmp/qemu-11.1.0/include/hw/arm/fsl-imx6ul.h'
text = open(hdr).read()
if 'MemoryRegion       iomuxc;' not in text:
    text = text.replace('    MemoryRegion       ocram;',
                        '    MemoryRegion       iomuxc;\n    MemoryRegion       ocram;', 1)
    open(hdr, 'w').write(text)

src = '/tmp/qemu-11.1.0/hw/arm/fsl-imx6ul.c'
text = open(src).read()
old = '''    /*
     * IOMUXC
     */
    create_unimplemented_device("iomuxc", FSL_IMX6UL_IOMUXC_ADDR,
                                FSL_IMX6UL_IOMUXC_SIZE);
    create_unimplemented_device("iomuxc_gpr", FSL_IMX6UL_IOMUXC_GPR_ADDR,
                                FSL_IMX6UL_IOMUXC_GPR_SIZE);
'''
new = '''    /*
     * IOMUXC: model as writable RAM so Linux pinctrl can program pad
     * configuration without hitting an unimplemented-device abort.
     */
    memory_region_init_ram(&s->iomuxc, OBJECT(dev), "imx6ul.iomuxc",
                           0x1000, &error_abort);
    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_IOMUXC_ADDR,
                                &s->iomuxc);
    create_unimplemented_device("iomuxc_gpr", FSL_IMX6UL_IOMUXC_GPR_ADDR,
                                FSL_IMX6UL_IOMUXC_GPR_SIZE);
'''
if old not in text:
    raise SystemExit('IOMUXC block not found')
text = text.replace(old, new, 1)
open(src, 'w').write(text)
print('patched')
