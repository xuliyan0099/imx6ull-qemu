# 正点原子 I.MX6ULL MINI QEMU 浏览器虚拟开发板

本项目模拟的是 **正点原子 I.MX6ULL MINI**（Alientek I.MX6U-MINI，eMMC 核心板），不是 NXP 官方 `mcimx6ul-evk` 参考板，也不是正点原子 ALPHA 大底板。更新日期为 2026-11-22。项目目录为 `D:\Workspace\StudyNote\IM6\qemu`，QEMU 机型名为 `mcimx6ull-alientek`，运行于 Windows + WSL2 Ubuntu-24.04。

当前已验证该板的出厂 Linux 自动显示原厂桌面、通过模拟触摸打开设置页，以及真机 FreeRTOS 图形固件显示 LVGL 并响应点击。当前状态和交接入口见 [HANDOFF](HANDOFF.md)，操作说明见 [浏览器使用手册](web/README.md)。

## 目标开发板



| 项目   | 正点原子 I.MX6ULL MINI                                   |
| ---- | ---------------------------------------------------- |
| 开发板  | 正点原子 I.MX6ULL MINI（I.MX6U-MINI，eMMC 版）               |
| 核心板  | ATK-CL6Y2CB，BTB 接口，eMMC 版本                           |
| SoC  | NXP MCIMX6Y2CVM08AB，ARM Cortex-A7，800MHz（实际约 792MHz） |
| 内存   | 512MB DDR3L                                          |
| 存储   | 8GB eMMC，另有 TF 卡接口                                   |
| 显示   | 1 路 RGB LCD；项目当前按 7 寸 800×480 桌面验证                   |
| 触摸   | Goodix 电容触摸；QEMU 使用 GT1158/gt9xx 兼容模型                |
| 网络   | 1 路 10/100M 以太网；QEMU 双 FEC + user-mode NAT，已实测 `10.0.2.15`、ping 网关/公网、HTTP 出站 |
| 声音   | MINI 无板载 codec；QEMU 增加 USB Audio（46f4:0002）和 `none/wav/alsa` 后端，guest 以 high-speed 枚举 |
| 其他外设 | USB Host/OTG、CAN、RS485、摄像头、SDIO WiFi、蜂鸣器、用户按键等       |

QEMU 机型名 `mcimx6ull-alientek` 沿用已有脚本，不再改名；它对应的目标板就是 **正点原子 I.MX6ULL MINI**。MINI 底板只引出一路 RJ45，因此 QEMU 里的双 FEC 只代表 SoC 模型能力，不代表实板有两个网口。



![出厂 Linux 原厂桌面](runs/official-hardware.png)

## 启动

双击 `scripts/run-virtual-board.cmd`，浏览器打开 `http://localhost:8765/`，选择配置后点击启动。本地调试优先双击 `scripts\run-virtual-board-gtk.cmd`，QEMU 通过 WSLg 打开原生 GTK 窗口，不走 VNC/noVNC。服务版本为 `2026-11-22-official-linux-netui-2`。启动器每次先结束本项目默认端口的上一次服务和 QEMU，再启动新服务。旧会话的临时磁盘写入随重启丢弃。



| 配置 ID               | 页面用途                    | QEMU 文件                              | 启动与输入                                    |
| ------------------- | ----------------------- | ------------------------------------ | ---------------------------------------- |
| `linux`             | BusyBox 测试              | `bin/qemu-system-arm-linux`          | U-Boot 从临时 vvfat 加载原厂内核、适配 DTB、initramfs |
| `linux-official`    | 正点原子 I.MX6ULL MINI 出厂系统 | `bin/qemu-system-arm-official-linux` | U-Boot 引导原厂内核及 rootfs，Goodix 中断触摸        |
| `freertos`          | eMMC 精简版                | `bin/qemu-system-arm-linux`          | U-Boot 裸块读取 OCRAM 程序，无图形应用               |
| `freertos-gui-emmc` | 真机图形 eMMC               | `bin/qemu-system-arm-graphics-linux` | U-Boot 加载两段固件，GDB 校验并完成原有 DDR 握手         |
| `freertos-gui`      | 真机图形 ELF                | `bin/qemu-system-arm-graphics-linux` | 直接加载 ELF，GDB 校验 DDR，轮询 GT1158            |

LCD 通过 QEMU VNC 和 noVNC 实时显示。鼠标采用清晰的箭头光标，三个图形配置开放指针输入。RESET 使用 QMP `system_reset`，暂停和继续使用 `stop`、`cont`。DS0 按 GPIO1\_IO03 的方向和数据寄存器采样。用户 KEY 尚未接线。

x86 Windows 上没有 ARM KVM，QEMU 只能 TCG 单 vCPU 模拟。默认已启用 `tb-size=512`、VNC `lossy=on`、noVNC 低画质 / 低压缩级别和 500 ms 状态轮询。官方 Linux 冷启动约 1 分 51 秒，FreeRTOS 图形配置约 100% 单核属于 guest 自身运行；如果本地觉得卡，优先用 GTK 启动器，性能取舍详见 [浏览器使用手册](web/README.md#性能取舍)。

启动器默认把 `IM6_IMAGE_DIR` 指向 `/opt/im6/images`，优先读取 WSL ext4 中的 rootfs；该目录不存在对应文件时回退到项目 `images/`。首次准备可运行 `bash scripts/setup-wsl-images.sh`，它只复制 2GB rootfs 和启动资产，8GB eMMC 基础镜像仍留在 D 盘。

## BeeLink 局域网部署

BeeLink（fnOS，Debian 12，Ryzen 7 7735HS）通过 Docker 常驻运行同一套网页虚拟板，局域网访问：



```
http://192.168.1.52:8765/    # WiFi
http://192.168.1.15:8765/    # Ethernet
```

项目数据放在 `/vol1/im6-qemu`，容器名为 `im6-qemu`，镜像为 `im6-qemu-runtime:latest`，启动策略 `--restart unless-stopped`。启动或重建：



```
ssh beelink "sudo bash /vol1/im6-qemu/deploy/beelink/run.sh"
# 强制重建镜像
ssh beelink "IM6_REBUILD=1 sudo bash /vol1/im6-qemu/deploy/beelink/run.sh"
```

`deploy/beelink/Dockerfile` 基于 Ubuntu 24.04，安装 QEMU 运行库、Python aiohttp、GTK3 依赖和 ARM GDB/objcopy；APT 走阿里云 HTTP 镜像，避免 BeeLink 访问 `archive.ubuntu.com` 只有约 32 KB/s。容器把 `/vol1/im6-qemu` 挂到 `/opt/im6`，端口 `0.0.0.0:8765`，`IM6_ALLOWED_HOSTS` 自动加入本机 IP。

BeeLink 是 x86 宿主，ARM guest 仍只能 TCG 单 vCPU，不使用 `/dev/kvm`。已在该机验证出厂 Linux 桌面（`runs/linux-beelink.jpg`）和 FreeRTOS LVGL 主界面（`runs/freertos-beelink.png`），两者均为 800×480、原厂 systemui/LVGL 实际帧缓冲截图。触摸、以太网沿用同一 QEMU 机型和模型；USB Audio 设备已加入，音频输出默认写 WAV，也可显式切到 BeeLink 的 ALSA 设备，摄像头、CAN 仍未完整模拟。



![BeeLink 出厂 Linux 桌面](runs/linux-beelink.jpg)



![BeeLink FreeRTOS LVGL 主界面](runs/freertos-beelink.png)

## 声音与以太网

**声音**：MINI 底板没有 WM8960 等板载 codec，正点原子官方也注明 MINI 音频需外接 USB 声卡。QEMU 因此走 USB Audio，而不是伪造 ALPHA 的 WM8960：

* QEMU 侧新增 `usb-audio` high-speed 支持；guest `lsusb` 可见 `46f4:0002`，内核日志为 `usb 1-1: new high-speed USB device`。
* `web/server.py` 支持 `IM6_AUDIO_BACKEND=none|wav|alsa`、`IM6_AUDIO_DEVICE=default|plughw:X,Y`、`IM6_AUDIO_FILE=/path/audio.wav`，并暴露 `/audio.wav`。
* BeeLink 有 `/dev/snd` 时 `run.sh` 可用 ALSA 并映射设备；默认用 `wav`，避免容器内无声卡时 QEMU 启动失败。
* 原厂 Linux 4.1.15 配置是 `CONFIG_SND_USB_AUDIO=m`，但 rootfs 的 `/lib/modules` 是空目录，没有对应 `.ko`，所以当前只完成 USB 设备枚举，guest 仍显示 `No soundcards found`。配置文件、模块版本和符号 CRC 都需与原厂内核一致，不能拿通用内核模块直接加载。要真正出声，需要原厂同源内核补编模块，或换一个内建 USB Audio Class 的内核；QEMU 侧和音频后端已就绪。

手动启用：

```
IM6_WEB_PORT=8766 IM6_AUDIO_BACKEND=wav IM6_AUDIO_FILE=/tmp/im6-audio.wav \
  PYTHONPATH=web/deps python3 web/server.py
# 或 BeeLink
IM6_AUDIO_BACKEND=alsa IM6_AUDIO_DEVICE=plughw:0,3 bash deploy/beelink/run.sh
```

**以太网**：机型保留 SoC 双 FEC，Linux profile 默认两条 `-nic user,model=imx.enet`，即 QEMU user-mode NAT。MINI 实板只保留一路百兆网口 **ENET2/FEC2**，对应 QEMU 的 `eth1`；`eth0` 是 FEC1，仅代表 SoC 能力，MINI 底板未引出。已实测 guest：

```
eth0  inet addr:10.0.2.15  Mask:255.255.255.0
eth1  inet addr:10.0.2.15  Mask:255.255.255.0
ping -c 2 10.0.2.2          # 2 received, 0% packet loss
busybox wget http://example.com/   # 577 bytes，出站 HTTP 通
```

网页板面新增 `03 / ETHERNET` 面板：显示 `ENET2 / FEC2 / eth1`、PHY `LAN8720A / SR8201F · RMII · addr 0x1`、`LINK UP`、`eth1 · 10.0.2.15`、`100Mbps/Full` 和 NAT 网关。`/api/status` 的 `net` 字段提供同一份状态。

**实板接线**：MINI 底板板载 RJ45（内置隔离变压器），用 Cat5e/6 直通网线接路由器或交换机即可；100BASE-TX 只用 1/2（TX）、3/6（RX）两对线，支持 Auto-MDIX，不需要交叉线。ENET1 在 MINI 底板未引出。QEMU 不需要物理网线，`eth1` 的 `10.0.2.15` 由 user-mode NAT 提供，网关 `10.0.2.2`。

这是出站 NAT，不是局域网桥接。若需要 guest 暴露到局域网，需宿主建 TAP/bridge 并给 QEMU 加权限，当前未默认启用。

## 正点原子 I.MX6ULL MINI 出厂 Linux 启动路径



```
Windows 启动器 → WSL aiohttp 服务 → QEMU BootROM → 现有 U-Boot
  宿主 loader 装载 zImage @ 0x80800000、图形 DTB @ 0x83000000
  U-Boot bootz → 原厂 Linux 4.1.15 → /etc/rc.local → 原厂 systemui
  浏览器指针 → VNC → Goodix @ I2C2 0x5d → GPIO1_IO09
             → 原厂 gt9xx → Linux input → 原厂 tslib → Qt
```

原厂内核 SHA-256 为 `93367b5f8da5bdf900bdef66e7689a86b42e9fe0b0be6c749bc927d84cf18230`，与用户提供的出厂目录一致。原厂 `rootfs.tar.bz2` 通过 `scripts/build-official-rootfs.sh` 打包为 ext4，运行时挂载到 `/dev/mmcblk0`。图形 DTB 基于项目适配版生成，LCD 位深设为 32 bpp。自动引导发送两条 U-Boot 命令，并回复串口终端尺寸查询。Linux 桌面由原厂脚本启动。详情见 [出厂 Linux 实现与踩坑记录](docs/official-linux-notes.md)。

## 已有验证



| 功能                      | 实现与证据                                                                       |
| ----------------------- | --------------------------------------------------------------------------- |
| BootROM / IVT / DCD     | 从 eMMC `0x400` 读取，历史日志有 60 次 DCD 写入                                         |
| 原厂内核进入 BusyBox          | `runs/official-linux-boot.log`                                              |
| 原厂桌面冷启动                 | `runs/official-hardware-validation.log`、`runs/official-hardware.png`        |
| 原厂触摸打开设置页               | `runs/official-hardware-touch.png`，驱动报告 800×480 中断模式                        |
| Linux 阶段零命令注入           | `runs/test_official_hardware.py` 断言及 `runs/official-hardware-serial-tx.bin` |
| FreeRTOS 图形与触摸          | `experiments/graphics/boot-test.log`、`experiments/graphics/screen.png`      |
| FreeRTOS eMMC、DS0、RESET | `web/tests/smoke_freertos.py`，已有启动和复位实测                                     |
| 图形 FreeRTOS eMMC、RESET  | `web/tests/smoke_graphics.py`，已有启动和复位实测                                     |
| USB Audio               | guest `lsusb` 见 `46f4:0002`，`usb 1-1: new high-speed USB device`；原厂内核配置有 `SND_USB_AUDIO=m` 但缺模块，故无声卡 |
| 以太网                     | 实板 `ENET2/FEC2` ↔ QEMU `eth1`，`10.0.2.15`；网页 `03 / ETHERNET` 显示 LINK UP/100Mbps/Full；NAT 网关 `10.0.2.2` |

证据对应各自测试阶段。文档更新期间进行了文件、入口和链接核对，系统运行结果沿用已有实测记录。

## 构建

在 WSL 项目目录运行对应入口。



```
cd /mnt/d/Workspace/StudyNote/IM6/qemu
bash scripts/build-official-rootfs.sh
bash scripts/build-qemu-official.sh
bash experiments/graphics/build.sh
```

rootfs 构建要求目标尚未存在，读取用户提供的出厂压缩包。两个 QEMU 构建入口使用独立的新目录，分别由 `IM6_OFFICIAL_BUILD`、`IM6_GRAPHICS_BUILD` 指定，默认位置及参数见 [HANDOFF](HANDOFF.md)。出厂 Linux QEMU 已完成增量编译及冷启动验证，两个新目录构建脚本的完整从零重建仍待回归。

基础版历史入口为 `scripts/build-qemu-patched.sh`。原 `000*.patch` 系列存在重叠及与独立机型源码不一致的情况，整理状态见 [HANDOFF](HANDOFF.md)。

## 运行数据与边界

网页会话在 `/tmp/im6-board-*` 创建独立 qcow2 overlay，正常关闭会丢弃会话写入。BusyBox 的 vvfat 也复制到会话目录。历史 GTK 和诊断脚本中有直接打开 raw 文件的命令，使用前应核对具体参数。



* Linux QMP 热复位曾循环进入 U-Boot，出厂图形配置的热复位尚待独立回归。

* 出厂 Linux 复测曾出现一次 `n_tty_receive_buf_common` 早期 Oops，后续冷启动通过，根因待定位。

* Goodix 为单点兼容模型，四角、拖动、长时间运行和完整复位地址选择仍待测试或实现。

* U-Boot 日志中的 `TFT7016 (1024x600)` 与 Linux 桌面实际 800×480 尚未统一，面板参数需按实板屏幕继续校准。

* DDR 采用寄存器及握手行为模拟，eMMC 使用 SD 卡语义替身；USB Audio 设备已枚举，但原厂内核没有 USB Audio Class 驱动，摄像头、CAN 等外设仍有缺口。

* 图形 FreeRTOS 依赖现有调试器加载许可握手，真板自主 eMMC 启动及同镜像刷写仍待实板验证。

## 仓库管理

仓库根为当前 `qemu/` 目录。`bin/`、`web/deps/`、8GB eMMC、2GB rootfs、QEMU 源码包和运行截图中间格式都不入库，规则见 `.gitignore`。

新机器拉取后先安装 Web 依赖：



```
bash scripts/setup-web-deps.sh
```

再下载固定版本 QEMU 源码：



```
bash scripts/fetch-qemu.sh
```

然后按 [镜像清单](images/README.md) 准备或生成启动资产，并按 [HANDOFF](HANDOFF.md) 构建 QEMU。仓库只保留源码、补丁、脚本、文档、测试记录和两个小型 DTB。

## 文档导航



| 文档                                                        | 内容                       |
| --------------------------------------------------------- | ------------------------ |
| [HANDOFF](HANDOFF.md)                                     | 接手顺序、实现映射、镜像地址、构建与故障边界   |
| [浏览器手册](web/README.md)                                    | 配置、接口、依赖、会话和测试操作         |
| [当前设计](docs/plans/2026-11-21-web-virtual-board-design.md) | 架构、协议、状态与数据流             |
| [计划执行对照](docs/plans/2026-11-21-web-virtual-board-plan.md) | 计划项到实际文件、验证与剩余项的映射       |
| [出厂 Linux 记录](docs/official-linux-notes.md)               | 原始镜像、显示根因、Goodix 与历史规避路径 |
| [FreeRTOS 图形实验](experiments/graphics/README.md)           | 真机固件、DDR 校验、GT1158 及实验构建 |