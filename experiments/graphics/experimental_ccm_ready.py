from pathlib import Path
p=Path('/tmp/im6-graphics-qemu/qemu-11.1.0/hw/misc/imx6ul_ccm.c');s=p.read_text();s=s.replace('    trace_ccm_read_reg(imx6ul_analog_reg_name(index), (uint32_t)value);','    if (offset == 0x150) value |= 0x80; /* oscillator ready for U-Boot */\n    trace_ccm_read_reg(imx6ul_analog_reg_name(index), (uint32_t)value);');p.write_text(s)
