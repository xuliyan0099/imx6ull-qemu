from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/mcimx6ull-alientek.c")
s = p.read_text()
s = s.replace("qdev_new(i == 1 ? TYPE_EMMC : TYPE_SD_CARD)", "qdev_new(TYPE_SD_CARD)")
p.write_text(s)
print("eMMC slot now uses SD-card semantics")
