# i.MX6ULL QEMU 交接文档

更新日期为 2026-11-21。项目位于 `D:\Workspace\StudyNote\IM6\qemu`，WSL 路径为 `/mnt/d/Workspace/StudyNote/IM6/qemu`。运行平台为 Windows + WSL2 Ubuntu-24.04，QEMU 基于 11.1.0，机型为 `mcimx6ull-alientek`。

当前服务版本为 `2026-11-21-official-linux-hardware-3`，版本常量位于 `web/server.py`。`web/launch.py` 每次执行都会重启默认会话。默认图形走 VNC/noVNC；设置 `IM6_DISPLAY=gtk` 时改走 WSLg 原生 GTK 窗口，`scripts/run-virtual-board-gtk.cmd` 是本地低延迟入口。

## 接手时先看

1. 阅读本文的配置表与已知问题，再查 [浏览器手册](web/README.md)。
2. 使用 `scripts/run-virtual-board.cmd` 打开本机浏览器开发板，按目标选择配置。
3. 修改出厂 Linux 时对照 `web/server.py`、`scripts/build-qemu-official.sh`、`src/im6-goodix-linux.c` 及 [Linux 记录](docs/official-linux-notes.md)。
4. 修改 FreeRTOS 图形适配时对照 `experiments/graphics/qemu-graphics.patch`、`experiments/graphics/build.sh` 和 [图形实验说明](experiments/graphics/README.md)。
5. 用已有测试保存串口和画面证据，按实测结果更新状态。

本文描述持久化文件和已验证能力。进程、端口和 `/tmp` 的内容需要接手时重新检查。最后一次出厂 Linux 回归已正常关闭测试会话。

## 当前配置

| profile | QEMU 二进制 | 卡及装载方式 | 输入与验证状态 |
| --- | --- | --- | --- |
| `linux` | `bin/qemu-system-arm-linux` | 临时 vvfat 放 zImage、适配 DTB、ramdisk；eMMC 用 U-Boot overlay | 已到 BusyBox shell，LCD Logo，指针只读 |
| `linux-official` | `bin/qemu-system-arm-official-linux` | rootfs ext4 overlay 在 SD index 0；U-Boot overlay 在 index 1；loader 装内核及 DTB | 原厂桌面与设置页已验证，Goodix 中断触摸 |
| `freertos` | `bin/qemu-system-arm-linux` | 既有 eMMC overlay；U-Boot 裸读 OCRAM 精简程序 | 调度、DS0、自动引导、RESET 已验证 |
| `freertos-gui-emmc` | `bin/qemu-system-arm-graphics-linux` | 真机构建的 boot/app 写入临时 eMMC，U-Boot 加载，GDB 校验并授予许可 | DDR 自检、LVGL、点击任务页、RESET 已验证 |
| `freertos-gui` | `bin/qemu-system-arm-graphics-linux` | `-kernel` 装载真机 ELF，GDB 校验 DDR 并授予许可 | 图形与触摸已有实验验证，复位需按目标配置核对 |

## 软件实现映射

| 功能 | 实际入口 | 关键行为 |
| --- | --- | --- |
| Windows 启动 | `scripts/run-virtual-board.cmd` | 启动 WSL launch 并打开 localhost 8765 |
| 服务版本更新 | `web/launch.py` | 按项目路径和默认端口识别旧服务及 QEMU，先终止旧会话，再启动新服务 |
| 配置和进程生命周期 | `web/server.py` 的 `Board.start/stop/watch` | 一个服务管理一个 QEMU，临时目录与 overlay，异常退出上报 |
| 自动引导 | `Board.begin_boot/auto_boot` | 独立队列消费串口，按提示符推进，超时转 manual |
| QMP | `Board.command` | greeting、capabilities、锁内逐条请求，跳过事件直到响应，5 秒读超时 |
| 串口 | `Board.read_serial`、`serial_ws` | 最多 128 KiB 历史，WebSocket 字节输出、文本输入，自动引导期间限制用户输入 |
| LCD 与指针 | `vnc_ws`、`web/static/app.js` | VNC TCP 与 WebSocket 代理，noVNC，图形配置开放指针 |
| 页面 | `web/static/index.html`、`web/static/style.css`、`web/static/app.js` | 板卡示意、800×480 LCD、串口、箭头光标、DS0、控制按钮 |
| DS0 | `Board.poll_led` | HMP `xp /2wx 0x0209c000` 读取 DR/GDIR，bit 3 输出且低电平时亮 |
| 用户 KEY | 页面占位 | GPIO 接线及输入处理待实现 |
| 出厂 Linux Goodix | `src/im6-goodix-linux.c` | I2C2 0x5d，GPIO1_IO09，单点帧队列及下降沿中断 |
| FreeRTOS GT1158 | `experiments/graphics/qemu-graphics.patch` | I2C2 0x14，固件轮询，单点状态及确认队列 |

当前后端集中在 `web/server.py`，计划中的 `session.py`、`qmp.py`、GPIO 桥模块等未独立拆分。串口采用 `<pre>` 和行输入。DS0 每约 150 ms 采样，页面每约 200 ms 查询状态。QMP 通过锁串行执行，当前没有请求 ID 分发器和完整异步事件状态同步。

## 出厂 Linux 的真实镜像边界

来源为用户目录 `D:\Workspace\IM6\【正点原子】阿尔法Linux开发板（A盘）-基础资料\08、系统镜像\01、出厂系统镜像`。

| 文件 | 用途与来源 |
| --- | --- |
| `images/u-boot.imx` | 沿用项目现有 U-Boot |
| `images/uboot-emmc.img` | 8 GiB raw 基础盘，U-Boot 位于 offset 0x400 |
| `images/zImage` | 出厂 Linux 4.1.15，6,792,144 字节 |
| `images/board-alientek-full.dtb` | 既有 QEMU 适配设备树，40,505 字节 |
| `images/board-alientek-official-gui.dtb` | 相对上述适配 DTB 唯一字节差异为 offset 29675 的 16 → 32，声明 LCD 32 bpp |
| `images/official-rootfs.ext4` | 原厂 rootfs.tar.bz2 经 fakeroot 和 mkfs.ext4 -d 打包的 2 GiB 文件系统 |
| `images/ramdisk.uimg` | BusyBox 配置所需 legacy uImage initramfs |
| `images/emmc-uboot-freertos.img` | 既有精简 FreeRTOS 基础盘 |

出厂 zImage 的 SHA-256 为 `93367b5f8da5bdf900bdef66e7689a86b42e9fe0b0be6c749bc927d84cf18230`。完整原厂 DTB 的直接兼容性仍待验证。

出厂 Linux 由宿主 loader 预置内核和 DTB，U-Boot 自动执行以下命令。

```text
setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0 rootwait rw
bootz 0x80800000 - 0x83000000
```

原厂 `/etc/rc.local` 加载 `/etc/profile` 并启动 `/opt/ui/systemui`，沿用软件渲染、linuxfb 和 tslib。宿主回复 ANSI 终端尺寸查询。回归断言已核对全部自动发送字节。Linux 阶段零命令注入的证据为 `runs/official-hardware-serial-tx.bin`。LCD 位域根因及历史 fbset/USB Tablet 方案见 [Linux 记录](docs/official-linux-notes.md)。

## 地址与存储布局

| 对象 | 偏移或装载地址 |
| --- | --- |
| DDR | 512 MiB，自 0x80000000 |
| UART1 | 0x02020000 |
| GPIO1 DR / GDIR | 0x0209c000 / 0x0209c004 |
| LCDIF | 0x021c8000 |
| I2C2 | 0x021a4000 |
| USDHC1 / USDHC2 | 0x02190000 / 0x02194000 |
| BootROM 读取 IVT | eMMC offset 0x400，magic 0x402000d1 |
| U-Boot entry | 0x87800000，历史 DCD 日志为 60 次写入 |
| Linux zImage / DTB | 0x80800000 / 0x83000000 |
| 精简 FreeRTOS | eMMC offset 0x100000 → OCRAM 0x00900000，go 0x900020 |
| 图形 FreeRTOS boot | 临时 eMMC offset 0x100000 → OCRAM 0x00900000 |
| 图形 FreeRTOS app | 临时 eMMC offset 0x200000 → DDR 0x80000000 |

FreeRTOS 图形构建来自 `D:\Workspace\FreeRTOS\IMX6ULL\build`。服务检查 manifest SHA-256，并对两段 ELF 通过 objcopy 重导出验证 BIN。eMMC 模式再回读 OCRAM 和 DDR 比较，最后通过 GDB 设置现有 `g_ddr_boot_status.load_permission=0x4c4f4144`。固件仍依赖这一加载许可握手。

## 构建入口与状态

WSL 在项目根目录运行。QEMU 源码包为 `../qemu-src/qemu-11.1.0.tar.xz`。

| 入口 | 输出与参数 | 验证范围 |
| --- | --- | --- |
| `scripts/build-official-rootfs.sh` | `images/official-rootfs.ext4`，目标已存在时退出，临时目录 `/tmp/im6-official-rootfs-*` | 已生成并用于冷启动 |
| `scripts/build-qemu-official.sh` | official 二进制及图形 DTB；`IM6_OFFICIAL_BUILD` 默认 `/tmp/im6-official-qemu` | 增量编译、运行及脚本语法通过，完整从零构建待回归 |
| `experiments/graphics/build.sh` | graphics 二进制；`IM6_GRAPHICS_BUILD` 默认 `/tmp/im6-graphics-rebuild` | 干净源码组合补丁应用已有验证，完整从零构建待回归 |
| `scripts/build-qemu-patched.sh` | 基础 linux 二进制；`BUILD` 默认 `/tmp/qemu-11.1.0-build` | 历史系列有重叠及源码不一致问题，待整理 |

两个图形构建入口都先应用 `qemu-graphics.patch`，再应用 `0002`、`0007`、`0009`。official 构建随后把 `src/im6-goodix-linux.c` 复制到构建树的 `hw/arm/im6-gt1158.c`，并替换机型接线为 0x5d + GPIO1_IO09。该文件名是沿用组合补丁的构建声明。official 二进制通过临时文件和 rename 更新。两个入口支持 `IM6_JOBS`，默认 4，并要求选择新的源码目录。

`src/mcimx6ull-alientek.c` 保留早期机型实现。新图形构建的机型内容来自组合补丁，后续修改需沿构建入口落实。原系列 `0008` 与 `0003/0005` 存在重叠，`0006` 与独立机型源文件存在差异。`0009` 修复大块 SDHCI DMA 跨边界行为，应保留对应行为。

## 补丁与历史入口映射

| 文件 | 对应行为 |
| --- | --- |
| `patches/0001-imx6ul-ccm.patch` | 基础 CCM / LCDIF 时钟选择 |
| `patches/0002-imx-gpt.patch` | GPT 时钟源映射 |
| `patches/0003-imx6ul-iomuxc-ram.patch` | IOMUXC 可写寄存器存储 |
| `patches/0005-imx6ul-iomuxc-snvs-gpr.patch` | IOMUXC/GPR/SNVS 地址覆盖 |
| `patches/0006-mcimx6ull-alientek-machine.patch` | 早期板级机型和 BootROM |
| `patches/0007-usdhc-uboot-compat.patch` | U-Boot 使用的 USDHC 命令、时钟、状态与 DMA 兼容 |
| `patches/0008-mmdc-reset-values.patch` | 早期 MMDC 512 MiB 复位值，存在与其他补丁重叠 |
| `patches/0009-sdhci-dma-boundary.patch` | 大块 DMA 跨边界继续传输 |
| `patches/linux-imx-4.1.15-qemu.patch` | 历史重编内核路径，输出 zImage-nxp-fb |
| `experiments/graphics/qemu-graphics.patch` | CCM、SoC、机型、LCDIF、GT1158 及 Meson 构建的组合来源 |

补丁编号没有 0004，基础脚本按已有 `000*.patch` 顺序应用。graphics 与 official 使用前文列出的组合补丁顺序。

| 历史脚本 | 当前文件中的参数和用途 |
| --- | --- |
| `scripts/run-uboot-linux.cmd` | 基础 QEMU，准备 /tmp/vvfat，GTK + 串口，U-Boot 手工引导原厂内核及 BusyBox |
| `scripts/run-freertos-emmc.cmd` | 基础 QEMU，直接打开精简 raw 镜像，U-Boot 手工 mmc read/go，watchdog-action none |
| `scripts/run-freertos.cmd` | 基础 QEMU，直接加载 build-qemu 的精简 ELF |
| `scripts/run-linux.cmd` | 基础 QEMU 直接加载 zImage-nxp-fb、initramfs，双 FEC，串口 |
| `scripts/run-linux-gui.cmd` | 上述重编内核路径增加 GTK |
| `scripts/run-linux-net.cmd` | 重编内核及 net-initramfs |
| `scripts/flash-freertos.cmd` | 运行历史 flash-initramfs，直接使用 images/emmc.img |
| `scripts/build-kernel-qemu.sh` | 克隆/使用 NXP Linux 源码，应用内核补丁，输出 zImage-nxp-fb |
| `scripts/run-linux.ps1` | Windows 原生 QEMU mcimx6ul-evk、原厂 DTB 和 emmc.img 的早期试验 |
| `scripts/run-hello.ps1`、`run-lcd.ps1` | Windows 原生 QEMU 的 baremetal hello / LCD 探针 |
| `run-hello.cmd`、`run-lcd.cmd`、`run-linux.cmd` | 根目录的对应 PowerShell 包装入口 |

历史脚本有直接打开 raw 镜像的参数，写入会落到该文件。网页入口的临时 overlay 行为由 `Board.start` 提供。当前出厂图形启动已使用原厂 zImage，历史重编内核路径用于保留探索和诊断。

BusyBox 手工引导需先将 zImage、board-alientek-full.dtb、ramdisk.uimg 放入 vvfat，按基础机型脚本运行后，在 U-Boot 执行以下命令。

```text
mmc dev 0
fatload mmc 0:1 0x80800000 zimage-official
fatload mmc 0:1 0x83000000 board-alientek-full.dtb
fatload mmc 0:1 0x84000000 ramdisk.uimg
setenv bootargs console=ttymxc0,115200 root=/dev/ram0 rw
bootz 0x80800000 0x84000000 0x83000000
```

`ramdisk.uimg` 需要 legacy uImage 包装，生成入口为 `runs/make_uimg_ramdisk.py`。精简 FreeRTOS 手工使用 `mmc dev 1`、`mmc read 0x900000 0x800 0x20`、`go 0x900020`。精简裸 BIN 的链接地址与 QEMU 默认 raw kernel 装载地址不同，应按已验证的 ELF 或 U-Boot 裸块路径运行。

`baremetal/` 为早期裸机探针，`initramfs/` 为精简、网络及刷写用户态材料，`runs/` 同时保存历史探索脚本与测试证据。出厂图形回归入口明确为 `runs/test_official_hardware.py`，旧 `runs/test_official_gui.py` 保留早期临时路径和等待方式，使用前需逐项核对。

## 回归与证据

```bash
cd /mnt/d/Workspace/StudyNote/IM6/qemu
PYTHONPATH=web/deps python3 runs/test_official_hardware.py
```

该测试直接创建独立 Board，默认 VNC display 92，即 TCP 5992，240 秒启动循环内检查早期 Oops、引导状态、Goodix 中断模式及全部串口发送字节。至少等到启动循环 120 秒后点击设置图标，再等 35 秒抓图，finally 关闭会话。脚本生成 PPM、串口日志和发送字节，PNG 转换及画面判断另行完成。`ready` 表示串口引导条件满足，完整桌面仍需画面确认。

其他回归针对已启动且空闲的服务运行。

```bash
python3 web/tests/smoke_freertos.py
python3 web/tests/smoke_graphics.py 8765
```

`smoke_freertos.py` 固定使用 8765，finally 会发送 stop，应先确认服务空闲。graphics 测试支持端口参数且先检查空闲。这两个脚本实际启动 QEMU。现有 `web/tests` 使用集成脚本，`unittest discover` 无法代替这些验证。

| 证据 | 验证内容 |
| --- | --- |
| `runs/official-hardware-validation.log` | 最终原厂 Linux 冷启动断言通过 |
| `runs/official-hardware-boot.log` | 内核、Goodix、原厂 init/rc.local 串口 |
| `runs/official-hardware-serial-tx.bin` | 两条 U-Boot 命令及一次 ANSI 回复 |
| `runs/official-hardware.png` | 原厂桌面 |
| `runs/official-hardware-touch.png` | 模拟触摸打开的完整设置页 |
| `experiments/graphics/boot-test.log` | DDR 自检、FreeRTOS、触摸与 LVGL |
| `experiments/graphics/screen.png` | FreeRTOS 任务页 |
| `runs/official-linux-boot.log` | 历史 BusyBox 启动 |
| `runs/freertos-emmc-boot.log` | 历史精简 FreeRTOS eMMC 启动 |

## 已知问题与后续工作

| 状态 | 影响与后续验证 |
| --- | --- |
| Linux 热复位未闭环 | BusyBox 路径曾循环回 U-Boot，出厂图形配置需独立定位与回归 |
| 一次早期串口 Oops | `n_tty_receive_buf_common`，后续冷启动通过，根因仍待定位 |
| 触摸覆盖有限 | Linux 已开设置页，FreeRTOS 已开任务页；四角、拖动、长时间运行、断线释放待验收 |
| Goodix 子集 | 单点、寄存器及事件队列可用，完整复位地址选择、固件更新、多点及电气时序待实现 |
| 用户 KEY 未连接 | 先核对可信原理图或固件接线，再实现输入及释放 |
| 存储与 DDR 简化 | SD 卡语义替身，DDR 寄存器行为及自检，完整 eMMC 和电气训练待扩展 |
| 原厂外设缺口 | 音频、摄像头、CAN、ADC 等完整链路待实现 |
| 原厂 DTB 兼容性 | 当前为 QEMU 适配版，需要逐项补硬件才能验证原始 DTB |
| 构建可重复性 | 两个新入口完整从零重建、基础补丁系列整理待完成 |
| 真板验证 | 同镜像刷写、自主图形 eMMC 启动尚待实板验证 |

## 会话和运行环境

默认 HTTP 监听 `127.0.0.1:8765`，VNC 监听 `127.0.0.1:5977`。手动启动 server 可通过 `IM6_WEB_PORT` 和 `IM6_VNC_DISPLAY` 修改，launch 固定连接 8765。QMP、UART 使用 `/tmp/im6-board-*/qmp` 和 `serial` Unix socket。正常关闭删除会话目录和 overlay，异常退出可能遗留临时目录。

依赖、接口、错误处理详见 [浏览器手册](web/README.md)，当前设计与计划映射见 [设计](docs/plans/2026-11-21-web-virtual-board-design.md) 和 [计划对照](docs/plans/2026-11-21-web-virtual-board-plan.md)。文档审校依据持久化代码及现有验证记录，本轮更新没有新增运行验收结论。


## 启动器重启行为验证

`web/launch.py` 使用项目路径散列命名的 `/tmp/im6-launch-*.lock` 串行处理启动。进程扫描检查脚本路径及 `IM6_WEB_PORT`，QEMU 检查项目二进制路径和默认 VNC 参数，发信号前再次检查归属。每次执行先结束旧默认服务和 QEMU，再 exec 新服务。SIGTERM 超时后采用强制终止，异常情况下临时目录可能遗留。

已实际验证连续两次启动同版本服务，中间启动精简 FreeRTOS。第二次启动后旧服务和旧 QEMU 退出，新服务处于 stopped 状态，其他端口的项目服务仍存活。Windows CMD 的浏览器打开步骤增加服务就绪轮询，完整 Windows 双击打开流程尚待本轮操作验证。
