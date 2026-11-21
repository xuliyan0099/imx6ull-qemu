# 镜像与启动资产清单

本目录只提交**小型、可直接用于启动的 DTB**。大镜像、厂商二进制和 QEMU 可执行文件不进入 Git，避免仓库膨胀到几十 GB。

入库判断原则：

- 源码、补丁、脚本、文档、测试记录必须入库；
- 40KB 级 DTB 可以直接入库；
- 单文件小于 10MB 的启动资产可以放 GitHub Release，不必进普通 Git；
- 2GB/8GB 镜像放外部存储，仓库只保留来源、大小和校验值；
- 8GB eMMC 镜像不要用 Git LFS，会耗尽配额。

## 已入库

| 文件 | 大小 | SHA-256 | 说明 |
| --- | ---: | --- | --- |
| `board-alientek-full.dtb` | 40,505 B | `303286AF1BE5A0C7721ABD5CA50A56A5E3BB5354A3E04CE2CBEE122335E83B18` | QEMU 适配 DTB，BusyBox/Linux 启动使用 |
| `board-alientek-official-gui.dtb` | 40,505 B | `AF4F7FAE5BA3736558B3919D7126DE4C4274A477657C2D1ABCE2269F3A73C92C` | 出厂图形系统使用，LCD 声明 32 bpp |

设备树源码在 `../runs/board-alientek-full.dts`、`../runs/board-alientek.dts`、`../runs/board-full.dts`，如需修改 DTB 应优先改 DTS 后重新编译。

## 不入库，放 Release 或外部存储

| 文件 | 大小 | SHA-256 | 来源 / 生成方式 |
| --- | ---: | --- | --- |
| `zImage` | 6,792,144 B | `93367B5F8DA5BDF900BDEF66E7689A86B42E9FE0B0BE6C749BC927D84CF18230` | 正点原子出厂 Linux 4.1.15，`08、系统镜像/01、出厂系统镜像/02、kernel镜像/.../zImage` |
| `u-boot.imx` | 449,536 B | `8635106B65BE41E376A484F53032C985CB14FC0DB8ACEC598A1E234B754C8191` | 正点原子 eMMC 版 U-Boot，本地构建产物 |
| `ramdisk.uimg` | 1,269,586 B | `73FE2B3FD7E296A709C6A21B89DA4638ADF559CE061522ACFC42F6D1BC73F256` | `runs/make_uimg_ramdisk.py` 用 legacy uImage 包装 |
| `official-rootfs.ext4` | 2,147,483,648 B | `E9A4AFD484EC618F725B85BA0A8FFC6B1610887D7BA98F27C71C0CBB346F3504` | `scripts/build-official-rootfs.sh` 从厂商 `rootfs.tar.bz2` 打包 |
| `tf.img` | 67,108,864 B | `EDAB2A03F72275E38F4154245AA99844D5F24FD3F8B872F5E69D3907CDC0C7C0` | 64MB TF 卡镜像，`truncate -s 64M images/tf.img` |
| `u-boot.bin` | 444,008 B | `0E33A0D95C6BCE2F0308F4E7B690E98CB2E7F81E408EB22B053E0D6695B12DF8` | U-Boot 构建中间产物 |
| `u-boot.elf` | 2,602,152 B | `B312EE0D9BC3DA2715934995FD8250BEC38C54A2F5205784C773C4BEF84EA988` | U-Boot ELF，调试用 |
| `zImage-nxp-fb` | 5,958,408 B | `96FCC75D8E7A2377C3FE0FA1B876D48FF8876D8EF5B0BE4F0DCBFE5EB390C8AE` | 历史重编内核，`scripts/build-kernel-qemu.sh` |
| `uboot-emmc.img` | 8,589,934,592 B | 不计算 | 8GB eMMC，仅 U-Boot @0x400 |
| `emmc-uboot-freertos.img` | 8,589,934,592 B | 不计算 | 8GB eMMC，U-Boot @0x400 + FreeRTOS @0x100000 |
| `emmc.img` | 8,589,934,592 B | 不计算 | 旧版 8GB eMMC，仅保留历史用途 |

8GB 文件体积过大，不做 SHA-256；如果需要校验，刷写后按实际文件重新计算并单独记录。

## 重新生成命令

### U-Boot + FreeRTOS eMMC

```bash
cd /mnt/d/Workspace/StudyNote/IM6/qemu

truncate -s 8G images/uboot-emmc.img
dd if=images/u-boot.imx of=images/uboot-emmc.img bs=512 seek=2 conv=notrunc

truncate -s 8G images/emmc-uboot-freertos.img
dd if=images/u-boot.imx of=images/emmc-uboot-freertos.img bs=512 seek=2 conv=notrunc
dd if=/mnt/d/Workspace/FreeRTOS/IMX6ULL/build-qemu/FreeRTOSIMX6ULL.bin \
   of=images/emmc-uboot-freertos.img bs=512 seek=2048 conv=notrunc
```

当前仓库没有独立的 `gen-emmc-image.py`，上面命令就是当前的生成依据。后续应把它脚本化，并加入 `FreeRTOSIMX6ULL.bin` 的 SHA-256 校验。

### 出厂 rootfs

```bash
bash scripts/build-official-rootfs.sh
```

脚本使用厂商目录：

```text
D:\Workspace\IM6\【正点原子】阿尔法Linux开发板（A盘）-基础资料\08、系统镜像\01、出厂系统镜像
```

目标 `images/official-rootfs.ext4` 已存在时脚本会拒绝覆盖，需要先确认旧文件是否还需要。

### ramdisk

```bash
# 先准备 /tmp/vvfat/initramfs.cpio.gz
python3 runs/make_uimg_ramdisk.py
cp /tmp/vvfat/ramdisk.uimg images/ramdisk.uimg
```

`ramdisk.uimg` 是 legacy uImage，不是裸 gzip；正点原子 U-Boot 的 `bootz` 只接受前者。

## 安全说明

- 不要提交厂商 rootfs、U-Boot、内核到公开仓库，先确认授权；
- 不要提交任何 8GB raw eMMC 镜像；
- 不要对真板整盘 `dd` 或重新分区，刷写前确认 `/dev/mmcblk1`；
- 公开仓库前检查 `runs/` 里是否含串口日志中的敏感信息、IP、密钥或账号。
