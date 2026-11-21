# i.MX6ULL 浏览器虚拟开发板当前设计

日期为 2026-11-21。本版按现有实现修订。已验证范围及剩余项见 [HANDOFF](../../HANDOFF.md)，计划执行对照见 [实施对照](2026-11-21-web-virtual-board-plan.md)。项目根目录为 `D:\Workspace\StudyNote\IM6\qemu`。

## 目标与实现范围

Windows 浏览器呈现板卡示意、800×480 LCD、UART、DS0、电源状态和 RESET，支持五种固定配置。当前已支持出厂 Linux 原厂桌面和 Goodix 触摸，以及真机 FreeRTOS LVGL 和轮询 GT1158。用户 KEY 和其他完整外设链路仍待扩展。

## 数据流

```text
scripts/run-virtual-board.cmd → web/launch.py → web/server.py
Windows 浏览器
  HTTP 状态与操作 → aiohttp → Board.start/stop/command
  串口 WebSocket ↔ Unix UART socket ↔ QEMU UART1
  noVNC WebSocket ↔ 本地 VNC TCP ↔ QEMU LCDIF 和输入分发
  DS0 状态 ← 定期 QMP/HMP 读取 GPIO1 DR/GDIR

QEMU mcimx6ull-alientek
  BootROM / IVT / DCD → U-Boot → Linux 或 FreeRTOS
  Linux 指针 → Goodix 0x5d → GPIO1_IO09 → gt9xx → tslib → Qt
  FreeRTOS 指针 → GT1158 0x14 → 固件轮询 → LVGL
```

## 服务与页面实现

| 设计职责 | 当前文件与方式 |
| --- | --- |
| 服务配置、会话、串口、QMP、VNC、GPIO 采样 | `web/server.py` 集中实现 |
| Windows 入口与上一次默认会话清理 | `scripts/run-virtual-board.cmd`、`web/launch.py` |
| UI | `web/static/index.html`、`style.css`、`app.js` |
| LCD 客户端 | 本地 noVNC 1.6.0，VNC binary WebSocket 代理 |
| 串口 UI | `<pre>` 输出与行输入 |
| 依赖 | `web/deps` 的 aiohttp 3.13.3 及其依赖 |

初稿中的 xterm.js、独立 session/qmp/serial/GPIO 模块尚未采用。当前 LCD 使用实时 VNC，截图用于验收记录。板卡布局为示意，箭头光标便于定位指针。

## 配置与磁盘

五种 profile 的二进制和装载路径见 [HANDOFF 配置表](../../HANDOFF.md)。每个服务管理一个 Board。每次启动创建专用临时目录，qcow2 分别覆盖基础 raw 镜像，vvfat 使用复制内容。正常关闭清除运行数据。会话持久化和恢复待实现。

`linux-official` 使用 `qemu-system-arm-official-linux`、出厂 zImage、出厂 rootfs 打包的 ext4 和独立图形 DTB。宿主 loader 把内核及 DTB 放到指定地址，U-Boot 执行 bootz。rootfs 挂载在 `/dev/mmcblk0`，原厂 rc.local 启动 systemui。图形 DTB 相对既有适配 DTB 仅将 LCD bpp 改为 32。

FreeRTOS 图形 eMMC 配置将真机构建的 boot/app 写入临时卡，U-Boot 装载，服务通过 GDB 校验内存并设置固件既有加载许可。ELF 配置直接加载 ELF 后执行 DDR 校验。实际文件与哈希检查集中于 `Board.start/auto_boot`。

## 状态和控制

服务状态包括 `stopped`、`starting`、`running`、`paused`、`stopping`、`error`。引导状态包括 `idle`、`booting`、`ready`、`manual`。`ready` 按串口条件产生，桌面完成绘制需要画面验收。

自动引导有独立串口队列，按提示符及预期结果推进。运行期间用户输入被限制，手动接管会取消引导任务。超时转 manual。RESET 先建立新引导任务，再发送 QMP system_reset。FreeRTOS 的复位已有实测，Linux 热复位仍有已知问题。

QMP 完成 greeting 和 capabilities，以锁串行发送请求，读取时跳过异步事件并等待 return/error。当前没有并发请求 ID 路由和完整事件驱动状态同步。串口保留最多 128 KiB，前端限制文本长度。VNC 和串口分别桥接至 WebSocket。

## GPIO 与触摸

DS0 对应 GPIO1_IO03，服务每约 150 ms 读取 DR/GDIR，输出且低电平时亮，输入或读取失败显示未知。网页每约 200 ms 查询服务状态，因此短脉冲可能漏采。

Linux Goodix 模型持久化在 `src/im6-goodix-linux.c`。I2C2 地址 0x5d、GPIO1_IO09 下降沿中断，支持 ID、配置尺寸、坐标就绪、单点坐标、状态确认及 32 帧队列。确认后先释放中断，再延迟产生下一帧下降沿，首次触摸先恢复高电平。

FreeRTOS GT1158 模型随 `qemu-graphics.patch` 构建，I2C2 地址 0x14，由原固件轮询。两个模型分别编入对应二进制。完整复位地址选择、多点、固件更新、电气时序以及断线释放仍待实现或验证。

## 接口与运行约束

HTTP 默认 127.0.0.1:8765，VNC 默认 127.0.0.1:5977。QMP、UART 为临时 Unix socket。server 支持通过环境变量修改 HTTP 和 VNC display，launch 固定使用 8765。接口、Host/Origin/token 校验及参数见 [浏览器手册](../../web/README.md)。

动作仅开放预定义配置、start、stop、pause、resume、reset、manual。HTTP 状态由页面定期查询。QEMU 异常退出由 watch 上报。正常服务退出调用 cleanup，强制中断及浏览器断线的完整清理覆盖仍需回归。

## 验收状态

已有原厂桌面及设置页画面、Linux 零命令注入断言、FreeRTOS DDR/图形/任务页、精简 DS0、精简及图形 eMMC RESET 的实测记录。四角与拖动、Linux 热复位、一次早期串口 Oops、长期稳定性、原始 DTB 和真板同镜像仍是后续项。具体证据文件见 [HANDOFF](../../HANDOFF.md)。
