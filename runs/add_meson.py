from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/arm/meson.build")
s = p.read_text()
old = "arm_common_ss.add(when: 'CONFIG_FSL_IMX6UL', if_true: files('fsl-imx6ul.c', 'mcimx6ul-evk.c'))"
new = "arm_common_ss.add(when: 'CONFIG_FSL_IMX6UL', if_true: files('fsl-imx6ul.c', 'mcimx6ul-evk.c', 'mcimx6ull-alientek.c'))"
assert old in s
p.write_text(s.replace(old, new))
print("meson updated")
