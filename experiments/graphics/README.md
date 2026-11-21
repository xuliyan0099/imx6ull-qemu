# 真机 FreeRTOS 图形固件适配

更新日期为 2026-11-21。该目录提供真机 FreeRTOS DDR/LCD/LVGL 固件的 QEMU 实验构建。项目根目录为 `D:\Workspace\StudyNote\IM6\qemu`，固件读取自 `D:\Workspace\FreeRTOS\IMX6ULL\build`。

## 两种启动路径

| profile | 装载过程 |
| --- | --- |
| `freertos-gui-emmc` | 临时 qcow2 写入 boot.bin @ 0x100000 和 app.bin @ 0x200000；U-Boot 分别读到 0x00900000 和 0x80000000，再 go 0x900020 |
| `freertos-gui` | QEMU -kernel 直接加载原有 FreeRTOSIMX6ULL.elf |

服务使用 `bin/qemu-system-arm-graphics-linux`，附加 GIC priority bits、GDB Unix socket 和 `-watchdog-action none`。固件 OCRAM 引导执行 DDR 初始化、自检，并等待调试器许可。服务检查 manifest SHA-256，eMMC 模式通过 objcopy 校验分段 ELF/BIN，并通过 GDB 回读 OCRAM 与 DDR 比较。通过后设置固件既有 `load_permission=0x4c4f4144`，应用进入 DDR 执行。

这一启动链依赖原固件的加载许可握手。真板上按该布局自主启动仍待设计与实测。所有网页写入位于临时 overlay，正常关闭丢弃。

## 已有验证

已有 DDR 自检、分段内存校验、FreeRTOS 调度、800×480 LCD、LVGL 9.2.2、GT115x 识别的日志。鼠标点击可进入任务页，图形 eMMC 配置的 QMP RESET 后自动引导已有验证。

| 文件 | 证据 |
| --- | --- |
| `experiments/graphics/boot-test.log` | DDR、FreeRTOS、GT115x 和 LVGL |
| `experiments/graphics/screen.png` | 任务页画面 |
| `web/tests/smoke_graphics.py` | 针对空闲 HTTP 服务的图形 eMMC 启动与 RESET 集成检查 |

中心及四角、按住拖动、断线释放、长期稳定性和 ELF 配置完整复位覆盖仍待回归。

## 构建与持久化来源

```bash
cd /mnt/d/Workspace/StudyNote/IM6/qemu
bash experiments/graphics/build.sh
```

`IM6_GRAPHICS_BUILD` 默认 `/tmp/im6-graphics-rebuild`，要求其中的源码目录尚未存在，`IM6_JOBS` 默认 4。源码包为 `../qemu-src/qemu-11.1.0.tar.xz`。脚本应用 `qemu-graphics.patch` 后再应用 `0002`、`0007`、`0009`，输出 graphics 二进制。

| 文件 | 当前职责 |
| --- | --- |
| `qemu-graphics.patch` | 组合构建来源，包含机型、DDR/时钟就绪行为、显示适配及 GT1158 模型 |
| `build.sh` | graphics 从新目录构建入口 |
| `im6-gt1158.c` | 独立模型探索副本，构建来源为组合补丁 |
| `experimental_*.py` | 探索阶段修改脚本 |
| `run-original-elf-test.py` | 直接 ELF 装载诊断脚本 |
| `web/server.py` | 当前网页启动、镜像检查、GDB 校验与许可逻辑 |

组合补丁曾在干净源码上验证应用并比对相应源文件。完整从零重建入口仍待回归。原基础 `000*.patch` 系列的重叠和源码差异见 [HANDOFF](../../HANDOFF.md)。

## 触摸模型范围

graphics 模型在 I2C2 地址 0x14，返回 GT1158 ID、800×480 配置、坐标状态和单点坐标，支持按下/移动/松开队列与状态确认。原 FreeRTOS 驱动轮询读取。完整芯片复位地址选择、中断、多点、固件更新和真实电气时序仍待实现。

## 与出厂 Linux 的构建关系

出厂 Linux 使用 `bin/qemu-system-arm-official-linux` 和 `scripts/build-qemu-official.sh`。official 构建复用本目录的组合补丁，再用 `src/im6-goodix-linux.c` 替换构建树内触摸源文件，并改接 I2C2 0x5d 和 GPIO1_IO09。Linux 原厂 gt9xx 驱动采用中断读取，原厂 tslib 交给 Qt。BusyBox 和精简 FreeRTOS 使用基础二进制。完整配置映射见 [HANDOFF](../../HANDOFF.md)。
