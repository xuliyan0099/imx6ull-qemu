from pathlib import Path
base=Path('/tmp/im6-graphics-qemu/qemu-11.1.0')
p=base/'include/hw/arm/fsl-imx6ul.h';s=p.read_text();s=s.replace('    MemoryRegion       analog;\n','    MemoryRegion       analog;\n    MemoryRegion       mdscr_io;\n    MemoryRegion       video_pll_io;\n    uint32_t           mdscr_value;\n    uint32_t           video_pll_value;\n');p.write_text(s)
p=base/'hw/arm/fsl-imx6ul.c';s=p.read_text();pos=s.index('static ')
func='''/* Minimal status handshakes; this is not DDR or PLL electrical simulation. */
static uint64_t im6_mdscr_read(void *opaque, hwaddr offset, unsigned size)
{
    FslIMX6ULState *s = opaque;
    return s->mdscr_value;
}
static void im6_mdscr_write(void *opaque, hwaddr offset, uint64_t value, unsigned size)
{
    FslIMX6ULState *s = opaque;
    s->mdscr_value = (value & ~(1u << 14)) | ((value & (1u << 15)) ? (1u << 14) : 0);
}
static const MemoryRegionOps im6_mdscr_ops = {
    .read = im6_mdscr_read, .write = im6_mdscr_write,
    .endianness = DEVICE_NATIVE_ENDIAN, .valid.min_access_size = 4, .valid.max_access_size = 4,
};
static uint64_t im6_video_pll_read(void *opaque, hwaddr offset, unsigned size)
{
    FslIMX6ULState *s = opaque;
    return s->video_pll_value;
}
static void im6_video_pll_write(void *opaque, hwaddr offset, uint64_t value, unsigned size)
{
    FslIMX6ULState *s = opaque;
    s->video_pll_value = value | (1u << 31);
}
static const MemoryRegionOps im6_video_pll_ops = {
    .read = im6_video_pll_read, .write = im6_video_pll_write,
    .endianness = DEVICE_NATIVE_ENDIAN, .valid.min_access_size = 4, .valid.max_access_size = 4,
};

'''
s=s[:pos]+func+s[pos:]
needle='    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_MMDC_CFG_ADDR,\n                                &s->mmdc);'
s=s.replace(needle,needle+'''\n    memory_region_init_io(&s->mdscr_io, OBJECT(dev), &im6_mdscr_ops, s, "im6.mdscr", 4);
    memory_region_add_subregion_overlap(&s->mmdc, 0x1c, &s->mdscr_io, 1);''')
needle='    memory_region_add_subregion(get_system_memory(), FSL_IMX6UL_ANALOG_ADDR,\n                                &s->analog);'
s=s.replace(needle,needle+'''\n    memory_region_init_io(&s->video_pll_io, OBJECT(dev), &im6_video_pll_ops, s, "im6.video_pll", 4);
    memory_region_add_subregion_overlap(&s->analog, 0xa0, &s->video_pll_io, 1);''')
p.write_text(s)
