# 浏览器虚拟开发板使用与接口

更新日期为 2026-11-21，当前服务版本为 `2026-11-21-official-linux-hardware-5`。项目根目录为 `D:\Workspace\StudyNote\IM6\qemu`，下文路径相对该目录。

## 启动与升级

Windows 双击 `scripts/run-virtual-board.cmd`。该脚本启动 Ubuntu-24.04 中的 `web/launch.py`，随后打开 `http://localhost:8765/`。launch 每次结束本项目默认 8765 服务及其默认 VNC 会话，再启动新服务，包括同版本服务。优先发送 SIGTERM 清理，等待 8 秒后强制结束残留服务，再清理 QEMU，超时后使用 SIGKILL。旧会话的临时磁盘写入随重启丢弃。启动脚本会等待服务可访问后打开浏览器，最多等待约 30 秒。服务更新后刷新页面以取得新令牌。

本地调试优先使用 GTK 原生窗口，绕过 VNC/noVNC：

```powershell
scripts\run-virtual-board-gtk.cmd
```

该脚本设置 `IM6_DISPLAY=gtk`，QEMU 通过 WSLg 直接打开窗口，鼠标不会被 VNC 代理和浏览器缩放拖慢。浏览器页面只保留串口、电源和状态控制，画面显示“LOCAL GTK WINDOW”。GTK 窗口关闭或服务停止后，下一次启动会清理旧 QEMU。

WSL 手动启动可使用以下命令。

```bash
cd /mnt/d/Workspace/StudyNote/IM6/qemu
IM6_IMAGE_DIR=/opt/im6/images PYTHONPATH=web/deps python3 web/server.py
```

默认 HTTP 端口为 8765，VNC display 为 77，即 TCP 5977。直接启动 server 时可设置 `IM6_WEB_PORT`、`IM6_VNC_DISPLAY`、`IM6_IMAGE_DIR`，Windows 启动器固定使用 8765、VNC display 77 和 `/opt/im6/images`。其他端口的服务继续独立运行。端口由其他程序占用时会报错。

音频相关变量：`IM6_AUDIO_BACKEND=none|wav|alsa`，默认 `wav`；`IM6_AUDIO_DEVICE=default|plughw:X,Y`；`IM6_AUDIO_FILE` 为 WAV 输出路径，默认 `runs/audio.wav`。Linux profile 会追加 `usb-audio` 设备。原厂 4.1.15 内核没有 `snd-usb-audio`，当前只能看到 USB 设备枚举，不能生成 sound card。

## 运行依赖

- WSL2 Ubuntu-24.04、Python 3.12、`qemu-img`、QEMU keymaps `/usr/share/qemu`、对应 QEMU 二进制和镜像。
- aiohttp 3.13.3 及依赖已放在 `web/deps`，对应 Python 3.12。发行版或 Python 版本变化后需核对二进制扩展兼容性。
- 新环境先执行 `bash scripts/setup-web-deps.sh` 重建 `web/deps`；该目录不入 Git，依赖版本见 `web/requirements.txt`。
- noVNC 1.6.0 位于 `web/static/vendor`，许可见该目录的 `LICENSE.txt`，Python 依赖许可见各 `.dist-info`。
- FreeRTOS 图形配置额外使用 `gdb-multiarch`，eMMC 图形配置还使用 `arm-none-eabi-objcopy` 和 `qemu-io`。
- rootfs 构建使用 `fakeroot`、tar、e2fsprogs，QEMU 构建使用 configure、Meson/Ninja、GTK、slirp 相关开发依赖及 `fdtput`。

## 配置选择

| 页面配置 | profile | 输入与启动行为 |
| --- | --- | --- |
| Linux / BusyBox 测试 | `linux` | U-Boot fatload 原厂内核、适配 DTB、ramdisk，串口 shell |
| Linux / 正点原子出厂系统（实验） | `linux-official` | 原厂桌面自动启动，原厂 tslib 通过 Goodix 模型接收指针 |
| FreeRTOS / eMMC 精简版 | `freertos` | 裸块读取到 OCRAM，调度和 LED，无图形应用 |
| FreeRTOS / 真机图形 eMMC（实验） | `freertos-gui-emmc` | 真机 boot/app 写临时卡，U-Boot 读取，GDB 校验与 DDR 许可 |
| FreeRTOS / 真机图形 ELF（实验） | `freertos-gui` | 直接装载真机 ELF，GDB DDR 校验与许可 |

镜像文件、二进制及装载地址完整映射见 [HANDOFF](../HANDOFF.md)。

出厂 Linux 启动时宿主 loader 将内核及图形 DTB 装入内存，服务仅在 U-Boot 中设置 bootargs 并执行 bootz。原厂 `/etc/rc.local` 启动 `/opt/ui/systemui`。终端尺寸查询由串口桥回复。原厂桌面及点击打开设置页已经验证，完整画面加载可能需要数分钟。`boot_state=ready` 依据串口标记，画面仍需观察。

## 控制与页面

LCD 来自 QEMU VNC，noVNC 按比例缩放。图形 Linux 和两个图形 FreeRTOS 配置允许指针输入，其他配置为 viewOnly。页面采用箭头鼠标，关闭 noVNC 的点状光标。

串口以 `<pre>` 展示输出，输入框按行发送。后端保留最多 128 KiB 输出，前端也限制显示文本长度。自动引导期间输入框禁用，可点击手动接管取消引导。超时或引导失败后进入 manual 状态并保留串口操作。

RESET 使用 QMP `system_reset`，暂停使用 `stop`，继续使用 `cont`。暂停状态需先继续运行才能复位，自动引导期间暂停会被拒绝。DS0 每约 500 ms 读取 GPIO1 的 DR/GDIR，bit 3 配置为输出且低电平时亮，输入或采样失败时显示未知。页面每约 500 ms 查询状态。用户 KEY 为未接线占位。

页面关闭按钮停止当前 QEMU，会丢弃该会话写入。关闭浏览器页签后，服务及 QEMU 可以继续运行。WSL 服务可通过 Ctrl+C 正常退出并执行清理。Windows 启动脚本启动的服务窗口应保留以便查看错误，强制关闭窗口的清理行为尚需独立验证。

## 会话数据

`Board.start` 为每次启动创建 `/tmp/im6-board-*`。eMMC、TF 和出厂 rootfs 使用独立 qcow2 overlay，BusyBox vvfat 内容复制到会话目录。正常 stop 删除目录与 overlay。异常退出可能遗留临时文件，清理前应确认对应 QEMU 已退出。当前会话写入按临时方式处理，持久化和恢复尚待实现。

## 服务接口映射

| 接口 | 实现与含义 |
| --- | --- |
| `GET /`、`GET /static/*` | 页面及本地资源 |
| `GET /token` | 当前服务令牌 |
| `GET /version` | 服务名、版本、launch_id、display 模式和 `audio` 后端 |
| `GET /api/status` | state、profile、error、boot_state、boot_message、led |
| `GET /api/serial` | 串口历史最后 12000 字节，便于脚本取证 |
| `GET /audio.wav` | WAV 后端的音频输出；文件不存在时 404 |
| `POST /api/start` | JSON profile，仅接受五种固定配置 |
| `POST /api/stop` | 停止并清理当前会话 |
| `POST /api/pause`、`resume`、`reset` | QMP 控制 |
| `POST /api/manual` | 取消自动引导 |
| `WS /ws/serial` | UART 字节输出及文本输入 |
| `WS /ws/vnc` | noVNC binary WebSocket 到本地 VNC 的代理，GTK 模式不使用 |

`/api` 和 `/ws` 校验 query token 或 `X-Token`。服务校验 Host 和存在的 Origin，仅接受当前 localhost/127.0.0.1 地址。后端集中在 `web/server.py`，QMP 使用锁内串行请求，响应处理中跳过事件。状态主要来自进程管理和 API 操作，完整 QMP 事件同步仍待实现。

## 验证命令

出厂 Linux 测试直接创建独立 Board 和临时 overlay，默认 VNC display 92，无需先启动 HTTP 服务。

```bash
PYTHONPATH=web/deps python3 runs/test_official_hardware.py
python3 runs/ppm2png_arg.py runs/official-hardware.ppm runs/official-hardware.png
python3 runs/ppm2png_arg.py runs/official-hardware-touch.ppm runs/official-hardware-touch.png
```

脚本检查冷启动、早期 Oops、Goodix 中断模式、全部自动发送字节，并注入设置图标的按下/松开事件。截图由人工确认原厂桌面及完整设置页。验证记录见 `runs/official-hardware-validation.log`，发送字节见 `runs/official-hardware-serial-tx.bin`。

FreeRTOS 测试面向已启动且空闲的 HTTP 服务。

```bash
python3 web/tests/smoke_freertos.py
python3 web/tests/smoke_graphics.py 8765
```

精简测试固定使用 8765，finally 会 stop 当前会话，执行前应确认空闲。图形测试支持端口参数且有空闲检查。已有实测覆盖自动启动、精简 DS0、精简及图形 eMMC RESET。上述脚本均需真实 QEMU，当前没有计划初稿所列的 unittest 单元测试文件。

## 镜像目录

默认从项目内 `images/` 读取镜像。Windows/WSL 启动器设置 `IM6_IMAGE_DIR=/opt/im6/images`，服务优先使用该目录，文件不存在时回退到项目 `images/`，所以可以只把热点镜像放进 WSL 的 ext4 虚拟盘，8GB eMMC 基础镜像继续留在 D 盘。

```bash
bash scripts/setup-wsl-images.sh
```

脚本会创建 `/opt/im6/images`，复制 2GB 出厂 rootfs、zImage、两个 DTB、ramdisk 和 `tf.img`；需要复制两套 8GB eMMC 基础镜像时加 `IM6_COPY_EMMC=1`。手工启动 server 时显式传入：

```bash
IM6_IMAGE_DIR=/opt/im6/images PYTHONPATH=web/deps python3 web/server.py
```

`/mnt/d` 是 WSL 的跨系统文件层，随机读比 ext4 慢；把 rootfs 放进 `/opt/im6/images` 主要改善出厂 Linux 冷启动和 rootfs 读取。画面卡顿仍优先按下一节的 GTK/原生 VNC 处理。

## 性能取舍

Windows x86 宿主没有 ARM KVM，QEMU 只能走 TCG 单 vCPU 软件模拟。当前默认参数：

- `-accel tcg,thread=multi,tb-size=512`，增大翻译块缓存，减少重复翻译。
- VNC 使用 `127.0.0.1`、`lossy=on`，只在本机传输，允许有损压缩降低带宽。
- noVNC `qualityLevel=4`、`compressionLevel=1`，以画质换延迟。
- 状态和 LED 轮询从 200/150 ms 放宽到 500 ms，减少浏览器与后端空转。
- eMMC/rootfs overlay 使用 `cache=unsafe`，临时会话数据本来就会丢弃；`linux` 的 vvfat 不加此选项。

在 Ryzen 7 PRO 8845HS + WSL2 上实测：官方 Linux 冷启动约 1 分 51 秒（调整前约 1 分 54 秒），桌面空闲 QEMU 约 10% CPU，VNC 指针探测约 5.1%；FreeRTOS 图形配置约 100% 单核 CPU，属于 guest 自身持续运行，不是 noVNC 单独造成。TCG 是主要上限，参数调整只能减少传输和轮询开销，不能把 ARM 模拟变成硬件虚拟化。

如果仍觉得卡，按以下顺序处理：

1. 本地调试改用 `scripts\run-virtual-board-gtk.cmd`，完全不经过 noVNC；这是目前最直接的低延迟方式。
2. 确认没有同时运行多个 QEMU；8GB eMMC 和 2GB rootfs 的 overlay 在机械盘或被杀毒软件扫描时会明显拖慢。
3. 需要浏览器页面时，本地也可以用原生 VNC 客户端连接 `127.0.0.1:5977`（display 77），绕过 noVNC 的 WebSocket 代理和浏览器缩放；QEMU 已启用 `lossy=on`。远程访问时才需要额外处理端口转发。
4. 需要接近真机速度，只能在 ARM 主机上用 KVM，或直接上真板；x86 Windows 无法给 ARM guest 提供 KVM。

## 故障与待验收项

| 现象 | 当前认识和处理入口 |
| --- | --- |
| 旧页面令牌失效 | 服务更换后刷新页面 |
| 启动失败 | 查看页面 error 和会话期间的 `qemu.log`，核对端口、依赖和镜像 |
| Linux 仅出现 Logo 或短暂黑屏 | 等待 QML 加载，结合串口与最终画面判断，见 Linux 记录 |
| Linux 热复位循环 | 已有历史复现，待定位；关闭再启动可走冷启动，但会丢弃 overlay |
| 早期串口 Oops | 出厂 Linux 复测出现过一次，后续冷启动通过，根因待定位 |
| 指针或外设覆盖 | 当前 Goodix 单点，四角、拖动、断线释放和长期稳定性待验收，用户 KEY 待接线 |

详细根因见 [Linux 记录](../docs/official-linux-notes.md)，FreeRTOS 相关限制见 [图形实验](../experiments/graphics/README.md)。
