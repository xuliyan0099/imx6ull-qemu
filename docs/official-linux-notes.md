# 正点原子出厂 Linux 实现与踩坑记录

更新日期为 2026-11-21。项目目录为 `D:\Workspace\StudyNote\IM6\qemu`。当前实现已验证原厂桌面自动启动及模拟触摸打开完整设置页。

## 当前实现映射

| 环节 | 文件或入口 | 实际行为 |
| --- | --- | --- |
| 原始资料 | 用户出厂系统目录 | 提供 zImage 和 rootfs.tar.bz2，沿用项目现有 U-Boot |
| rootfs 打包 | `scripts/build-official-rootfs.sh` | fakeroot 解包并用 mkfs.ext4 -d 生成 2 GiB ext4 |
| QEMU 构建 | `scripts/build-qemu-official.sh` | 组合补丁及 0002/0007/0009，再替换 Goodix 模型和接线 |
| 触摸源文件 | `src/im6-goodix-linux.c` | GT1158 单点兼容模型，I2C2 0x5d，GPIO1_IO09 |
| 启动及串口桥 | `web/server.py` | overlay、loader、U-Boot 自动引导、ANSI 回复 |
| 图形设备树 | `images/board-alientek-official-gui.dtb` | LCD 32 bpp，基于既有 QEMU 适配 DTB |
| 原厂用户态 | `/etc/rc.local`、`/etc/profile`、`/opt/ui/systemui` | 原厂开机脚本、软件渲染、linuxfb、tslib |
| 回归 | `runs/test_official_hardware.py` | 冷启动、Goodix、中断、发送字节断言、点击及抓图 |

## 镜像来源与边界

用户提供的出厂目录为 `D:\Workspace\IM6\【正点原子】阿尔法Linux开发板（A盘）-基础资料\08、系统镜像\01、出厂系统镜像`。

内核来自该目录的 `02、kernel镜像/linux-imx-4.1.15-2.1.0-e48931b1-v2.8/zImage`，与项目 `images/zImage` 的 SHA-256 相同。

```text
93367b5f8da5bdf900bdef66e7689a86b42e9fe0b0be6c749bc927d84cf18230
```

根文件系统来自 `03、文件系统/rootfs.tar.bz2`，此前已与烧录工具副本核对 SHA-256 一致。烧录工具目录中的 zImage 与本次出厂内核存在差异，因此镜像来源应逐项核对。

`images/official-rootfs.ext4` 是原厂文件内容的文件系统容器，运行时以临时 qcow2 overlay 挂载到 `/dev/mmcblk0`。基础 eMMC 的 U-Boot 同样使用 overlay。图形 DTB 基于既有适配版，长度均为 40,505 字节，相对该版本唯一字节差异为 offset 29675 的 16 → 32。完整原厂 DTB 直接运行仍待验证。

## LCD 位域问题的根因

对照原厂 Linux 4.1.15 v2.8 的 `drivers/video/fbdev/mxsfb.c`。原厂 800×480 DTB 和既有模拟适配 DTB 声明 LCD 16 bpp。初始化先由 `mxsfb_check_var()` 填入 RGB565 位域。随后 `mxsfb_restore_mode()` 尝试接管 U-Boot 留下的运行中 LCDIF，根据 CTRL.WORD_LENGTH 将 bits_per_pixel 更新为 32，并修改行跨度，颜色位域仍保留早先状态。

U-Boot 串口报告 1024×600×24，原 Linux fbset 曾读到 32 位配 `5/11,6/5,5/0`，Qt 出现 QPainter 绘制错误。实测先切 16 位再切 32 位后，正常模式设置路径会重算 RGB 位域。该问题集中在启动接管路径。QEMU 保留 U-Boot 运行态，使当前组合触发了这一状态，真板相同组合是否复现仍待验证。

当前图形 DTB 直接声明 32 bpp，使最初的 check_var 建立 RGB888 位域，与接管后的位深匹配。出厂内核仍使用经哈希核对的镜像。驱动层修正可在 restore_mode 中统一更新位深、位域和行跨度，当前采用宿主侧适配 DTB。

迁移 rootfs 到 WSL 本地磁盘的早期试验没有单独解决画面问题。现有证据将该画面故障定位到帧缓冲格式，磁盘性能需要独立测量。

## 自动启动和零命令注入

宿主 loader 装载 zImage 到 0x80800000、图形 DTB 到 0x83000000。U-Boot 自动执行两条命令。

```text
setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0 rootwait rw
bootz 0x80800000 - 0x83000000
```

原厂 rc.local 加载 profile 并启动 systemui。串口登录过程会发送 ANSI 光标位置查询，宿主回复 `ESC[30;100R`，避免等待终端尺寸。

最终回归记录的全部自动发送字节为上述两条命令及一次 ANSI 回复。测试剔除 ANSI 回复后做精确字节断言，确认 Linux 阶段零命令注入。`boot_state=ready` 在串口提示符后设置，完整画面仍需等待 QML 加载并检查截图。

原厂 psplash 显示开机 Logo。进入串口或看到 Logo 属于启动阶段证据，完整桌面和应用页由最终画面确认。原厂应用加载期间可能短暂黑屏或显示空白页面，最后一次设置页抓图在点击后等待了 35 秒。

## Goodix 中断触摸

Linux 使用 `im6-goodix-linux` 模型，I2C2 地址 0x5d，IRQ 接 GPIO1_IO09。原厂驱动识别 ID 1158、800×480 和下降沿触发，注册 goodix-ts 输入设备，并报告 interrupt mode。原厂 udev/tslib 路径将触摸交给 Qt。

| 寄存器或行为 | 模型覆盖 |
| --- | --- |
| 0x8140 起 | 产品 ID 1158 |
| 0x8048 起、0x8051 起 | 配置读取中的 800×480 尺寸 |
| 0x804d、0x8056 | 下降沿触发配置 |
| 0x814e | 坐标就绪及触点数量，写零确认 |
| 0x8150–0x8154 | 单点 X/Y 及触点宽度 |
| 输入队列 | 最多 32 帧，按下、移动、松开 |
| 中断 | 首帧先恢复高电平，延迟产生下降沿，确认后释放并延迟下一帧 |
| QEMU 系统复位 | 清理队列、坐标及定时器，恢复空闲 IRQ |

原厂驱动复位期间会主动拉低 INT。首帧需要先恢复高电平再产生下降沿，才能覆盖该状态。坐标确认后的下一次中断也需留出驱动工作队列重新开放 IRQ 的时间。

当前子集已验证打开完整设置页。多点、触摸固件更新、完整物理复位地址选择和电气时序仍待实现，四角、拖动、断线释放和长期运行待回归。FreeRTOS 的轮询 GT1158 模型位于 graphics 组合补丁，地址为 0x14，详见 [图形实验](../experiments/graphics/README.md)。

## 历史规避方案

早期网页曾在串口登录后执行 fbset，退出 psplash 并重新启动 systemui，同时关闭 tslib，使用 USB Tablet 和 Qt evdevmouse 的 `:abs` 选项。该路径用于确认帧缓冲与指针问题。现有 `linux-official` 配置采用图形 DTB 与 Goodix 模型，启动映射见本页前文。

## 验证文件

| 文件 | 作用 |
| --- | --- |
| `runs/official-hardware-validation.log` | 最终冷启动、原厂 Goodix probe 和零命令注入断言通过 |
| `runs/official-hardware-boot.log` | 原厂内核、驱动、init 与 rc.local 串口 |
| `runs/official-hardware-serial-tx.bin` | 全部自动发送字节 |
| `runs/official-hardware.png` | 自动进入原厂桌面 |
| `runs/official-hardware-touch.png` | 模拟触摸打开完整设置页 |
| `runs/official-hardware.ppm`、`official-hardware-touch.ppm` | 测试生成的原始截图 |

测试命令与截图转换入口见 [浏览器手册](../web/README.md)。最终回归使用全新 overlay，完成后已关闭测试会话。截图的完整页面由人工检查，脚本自动检查引导、驱动和发送字节。

## 未定位和待扩展项

复测曾出现一次 `n_tty_receive_buf_common` 早期内核 Oops，后续冷启动通过，根因仍待定位。Linux QMP 热复位曾在早期配置循环回 U-Boot，当前出厂图形配置仍需独立回归。完整从零 QEMU 重建、长期稳定性、原始 DTB、完整 eMMC 协议以及音频/摄像头等外设链路仍是后续工作。

本轮文档更新对照了现有源文件、脚本及持久化证据，运行结论沿用此前实际验证。
