from pathlib import Path
base=Path('/tmp/im6-graphics-qemu/qemu-11.1.0')
p=base/'include/hw/arm/fsl-imx6ul.h';s=p.read_text();s=s.replace('    MemoryRegion       video_pll_io;','    MemoryRegion       video_pll_io;\n    MemoryRegion       anatop_ready_io;\n    uint32_t           anatop_ready_value;');p.write_text(s)
p=base/'hw/arm/fsl-imx6ul.c';s=p.read_text();idx=s.index('static uint64_t im6_video_pll_read')
s=s[:idx]+'''static uint64_t im6_anatop_ready_read(void *opaque, hwaddr offset, unsigned size)
{
    FslIMX6ULState *s = opaque;
    return s->anatop_ready_value | 0x80;
}
static void im6_anatop_ready_write(void *opaque, hwaddr offset, uint64_t value, unsigned size)
{
    FslIMX6ULState *s = opaque;
    s->anatop_ready_value = value;
}
static const MemoryRegionOps im6_anatop_ready_ops = {
    .read = im6_anatop_ready_read, .write = im6_anatop_ready_write,
    .endianness = DEVICE_NATIVE_ENDIAN, .valid.min_access_size = 4, .valid.max_access_size = 4,
};
''' + s[idx:]
n='    memory_region_add_subregion_overlap(&s->analog, 0xa0, &s->video_pll_io, 1);'
s=s.replace(n,n+'\n    memory_region_init_io(&s->anatop_ready_io, OBJECT(dev), &im6_anatop_ready_ops, s, "im6.anatop_ready", 4);\n    memory_region_add_subregion_overlap(&s->analog, 0x150, &s->anatop_ready_io, 1);');p.write_text(s)
