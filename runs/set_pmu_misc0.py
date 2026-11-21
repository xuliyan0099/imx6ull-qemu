from pathlib import Path

p = Path("/tmp/qemu-11.1.0/hw/misc/imx6ul_ccm.c")
s = p.read_text()
old = "    s->analog[PMU_MISC0] = 0x04000000;"
new = "    s->analog[PMU_MISC0] = 0x04000080;"
if old not in s:
    raise SystemExit("PMU_MISC0 reset line not found")
p.write_text(s.replace(old, new, 1))
print("PMU_MISC0 REFTOP_VLD set")
