from pathlib import Path

src = Path("/tmp/qemu-11.1.0/hw/arm/mcimx6ul-evk.c").read_text()
src = src.replace("mcimx6ul_evk", "mcimx6ull_alientek")
src = src.replace('DEFINE_MACHINE_ARM("mcimx6ul-evk", mcimx6ull_alientek_machine_init)',
                  'DEFINE_MACHINE_ARM("mcimx6ull-alientek", mcimx6ull_alientek_machine_init)')
src = src.replace('mc->desc = "Freescale i.MX6UL Evaluation Kit (Cortex-A7)";',
                  'mc->desc = "Alientek I.MX6ULL Mini (Cortex-A7, eMMC + 7in LCD)";')
src = src.replace("carddev = qdev_new(TYPE_SD_CARD);",
                  "carddev = qdev_new(i == 1 ? TYPE_EMMC : TYPE_SD_CARD);")
Path("/tmp/qemu-11.1.0/hw/arm/mcimx6ull-alientek.c").write_text(src)
print("created")
