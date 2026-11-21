#!/usr/bin/env python3
"""Apply the i.MX6ULL QEMU audio/touch changes to a prepared QEMU tree.

Run from the QEMU source root after qemu-graphics.patch and the i.MX patches:
    python3 scripts/patch-qemu-audio.py .
"""
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()


def replace_once(path, old, new, label):
    text = path.read_text()
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"{label}: pattern not found in {path}")
    path.write_text(text.replace(old, new, 1))


machine = root / "hw/arm/mcimx6ull-alientek.c"
text = machine.read_text()
if '#include "hw/i2c/i2c.h"' not in text:
    text = text.replace('#include "hw/arm/boot.h"',
                        '#include "hw/arm/boot.h"\n#include "hw/i2c/i2c.h"', 1)
if '"im6-goodix-linux"' not in text:
    if '"im6-gt1158", 0x14' in text:
        text = text.replace(
            'i2c_slave_create_simple(s->i2c[1].bus, "im6-gt1158", 0x14);',
            'i2c_slave_create_simple(s->i2c[1].bus, "im6-goodix-linux", 0x5d);')
    else:
        marker = '    qdev_realize(DEVICE(s), NULL, &error_fatal);\n'
        if marker not in text:
            raise SystemExit("touch insertion point not found")
        text = text.replace(marker, marker + '''    I2CSlave *touch = i2c_slave_create_simple(s->i2c[1].bus,
                                               "im6-goodix-linux", 0x5d);
    qdev_connect_gpio_out(DEVICE(touch), 0,
                          qdev_get_gpio_in(DEVICE(&s->gpio[0]), 9));
''', 1)
machine.write_text(text)

meson = root / "hw/arm/meson.build"
text = meson.read_text()
if "im6-gt1158.c" not in text:
    text = text.replace("'mcimx6ull-alientek.c'", "'mcimx6ull-alientek.c', 'im6-gt1158.c'", 1)
    meson.write_text(text)

audio = root / "hw/usb/dev-audio.c"
text = audio.read_text()
if "static const USBDescDevice desc_device = {" in text:
    text = text.replace("static const USBDescDevice desc_device = {\n    .bcdUSB                        = 0x0100,",
                        "static const USBDescDevice desc_device = {\n    .bcdUSB                        = 0x0200,", 1)
if ".high = &desc_device" not in text:
    text = text.replace("    .full = &desc_device,\n    .str",
                        "    .full = &desc_device,\n    .high = &desc_device,\n    .str", 1)
if "dev->speed = USB_SPEED_HIGH;" not in text:
    text = text.replace("    usb_desc_init(dev);\n    s->dev.opaque = s;",
                        "    usb_desc_init(dev);\n    dev->speed = USB_SPEED_HIGH;\n    s->dev.opaque = s;", 1)
audio.write_text(text)

desc = root / "hw/usb/desc.c"
replace_once(desc,
             "    dev->speed = USB_SPEED_FULL;\n    dev->speedmask = 0;",
             "    dev->speed = desc->high ? USB_SPEED_HIGH : USB_SPEED_FULL;\n    dev->speedmask = 0;",
             "desc speed selection")

regs = root / "include/hw/usb/ehci-regs.h"
text = regs.read_text()
if "PORTSC_HIGH_SPEED" not in text:
    text = text.replace("#define PORTSC_CONNECT       (1 << 0)",
                        "#define PORTSC_CONNECT       (1 << 0)\n#define PORTSC_HIGH_SPEED    (1 << 27)", 1)
if "0x007001c0" in text:
    text = text.replace("0x007001c0", "0x087001c0", 1)
regs.write_text(text)

ehci = root / "hw/usb/hcd-ehci.c"
text = ehci.read_text()
old_attach = "    *portsc |= PORTSC_CONNECT;\n    *portsc |= PORTSC_CSC;\n"
new_attach = old_attach + "    if (port->dev->speed == USB_SPEED_HIGH) {\n        *portsc |= PORTSC_HIGH_SPEED;\n    }\n"
if "PORTSC_HIGH_SPEED" not in text:
    if old_attach not in text:
        raise SystemExit("EHCI attach point not found")
    text = text.replace(old_attach, new_attach, 1)
old_detach = "    *portsc &= ~(PORTSC_CONNECT | PORTSC_PED | PORTSC_SUSPEND);\n"
new_detach = "    *portsc &= ~(PORTSC_CONNECT | PORTSC_PED | PORTSC_SUSPEND |\n                 PORTSC_HIGH_SPEED);\n"
if old_detach in text:
    text = text.replace(old_detach, new_detach, 1)
ehci.write_text(text)

print("audio patches applied")
