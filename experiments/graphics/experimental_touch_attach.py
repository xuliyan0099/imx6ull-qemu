from pathlib import Path
base=Path('/tmp/im6-graphics-qemu/qemu-11.1.0/hw/arm')
p=base/'mcimx6ull-alientek.c';s=p.read_text();s=s.replace('#include "hw/arm/boot.h"','#include "hw/arm/boot.h"\n#include "hw/i2c/i2c.h"');s=s.replace('    qdev_realize(DEVICE(s), NULL, &error_fatal);','    qdev_realize(DEVICE(s), NULL, &error_fatal);\n    i2c_slave_create_simple(s->i2c[1].bus, "im6-gt1158", 0x14);');p.write_text(s)
p=base/'meson.build';s=p.read_text().replace("'mcimx6ull-alientek.c'))", "'mcimx6ull-alientek.c', 'im6-gt1158.c'))");p.write_text(s)
