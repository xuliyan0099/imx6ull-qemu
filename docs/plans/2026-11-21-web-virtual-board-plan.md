# 浏览器虚拟开发板实施计划执行对照

更新日期为 2026-11-21。目标为在本机浏览器操作真实 QEMU LCD、UART、RESET、DS0 和图形系统触摸。本文将原计划映射到当前持久化代码，状态依据现有日志与画面。项目根目录为 `D:\Workspace\StudyNote\IM6\qemu`。

当前架构见 [设计](2026-11-21-web-virtual-board-design.md)，接手细节见 [HANDOFF](../../HANDOFF.md)。本轮文档审校沿用已有运行记录。

## 计划项到实现的映射

| 原计划项 | 实际落点 | 当前状态与剩余项 |
| --- | --- | --- |
| 0 基线及选型 | 基础 QEMU、noVNC、aiohttp、已有 runs 日志 | VNC 与本机浏览器可用，完整基础补丁重建待整理 |
| 1 服务骨架 | `web/server.py`、`web/deps` | 静态资源、token、Host/Origin、固定 profile 已实现，专门的异常和边界单元测试待补 |
| 2 会话与镜像管理 | `Board.start/stop/watch` | 单实例、临时目录、qcow2、vvfat 副本已实现，持久化与恢复待实现 |
| 3 QMP 与串口 | `Board.command/read_serial/auto_boot`、`serial_ws` | 握手、串行命令、引导队列、manual、有限历史已实现，完整事件同步待扩展 |
| 4 浏览器与 LCD | `web/static`、`vnc_ws`、`scripts/run-virtual-board.cmd`、`web/launch.py` | noVNC 实时 LCD、控制、行输入、箭头光标、旧会话自动终止并重启已实现 |
| 5 DS0 | `Board.poll_led`、`app.js` | DR/GDIR 采样并按低有效显示，精简 FreeRTOS 已验证，短脉冲可能漏采 |
| 6 第一阶段回归 | `web/tests/smoke_freertos.py`、`smoke_graphics.py`、runs 证据 | 多项集成验证已有记录，完整原计划验收仍有剩余 |
| 7 真机 FreeRTOS 图形及 GT1158 | `experiments/graphics`、`Board.start/auto_boot` | DDR 校验、LVGL、单点点击和图形 eMMC RESET 已验证，四角拖动及实板自主启动待完成 |
| 8 用户 KEY 及其他外设 | 页面占位 | KEY 接线、音频、摄像头等完整链路待实现 |
| 新增出厂 Linux 桌面 | `scripts/build-official-rootfs.sh`、`Board.start/auto_boot`、图形 DTB | 原厂 rootfs、桌面及零 Linux 命令注入冷启动已验证 |
| 新增 Linux 原厂触摸 | `src/im6-goodix-linux.c`、`scripts/build-qemu-official.sh` | Goodix 中断模式与打开完整设置页已验证 |

## 与初稿的实现调整

| 初稿设想 | 当前实现 |
| --- | --- |
| session/config/qmp/serial/vnc 独立模块 | 后端集中于 `web/server.py` |
| xterm.js 终端 | `<pre>` 输出和行输入 |
| QMP 请求 ID 分发、完整事件同步 | 锁内串行请求，跳过事件等待响应 |
| GPIO 独立桥接与 0010 补丁 | QMP/HMP 读取 GPIO DR/GDIR |
| profile `freertos-emmc` | 实际 ID 为 `freertos`，另有两个图形 profile |
| overlay 可选保留 | 正常关闭删除临时会话 |
| 单套补丁构建 | 基础、graphics、official 三个二进制，两个图形构建入口 |
| unittest discover 验收 | 当前测试为显式执行的集成脚本及画面检查 |
| 首期触摸等待后续 | FreeRTOS 轮询模型及 Linux 中断模型均有实现和有限验证 |

## 已有验证与复核方式

| 验证 | 入口或证据 | 覆盖范围 |
| --- | --- | --- |
| 精简 FreeRTOS | `web/tests/smoke_freertos.py` | 启动、DS0 亮灭、RESET 和再次引导 |
| 图形 FreeRTOS eMMC | `web/tests/smoke_graphics.py` | 分段内存校验、图形引导、RESET |
| FreeRTOS 交互画面 | `experiments/graphics/screen.png` | 任务页 |
| 出厂 Linux | `runs/test_official_hardware.py` | 新 overlay 冷启动、Oops 检查、Goodix 中断、发送字节断言及点击抓图 |
| 出厂 Linux 结果 | `runs/official-hardware-validation.log`、`official-hardware-serial-tx.bin` | 自动输入止于 U-Boot，另有 ANSI 回复 |
| 原厂桌面与设置页 | `runs/official-hardware.png`、`official-hardware-touch.png` | 人工视觉确认 |

运行命令、端口与空闲要求见 [浏览器手册](../../web/README.md)。出厂测试生成 PPM，PNG 转换另行执行。图形页面完成渲染需要画面确认，串口 ready 是引导阶段标记。

## 后续执行顺序

1. 定位 Linux 早期串口 Oops 与热复位循环，分别保存重现条件、日志和回归结果。
2. 在新目录完整运行 official 和 graphics 构建入口，整理基础补丁重叠、独立源码和组合补丁的一致性。
3. 验证触摸四角、中心、按住、拖动、松开、断线恢复与长期运行，补充必要的模型行为。
4. 核对用户 KEY 接线后实现 GPIO 输入，逐步补其他外设。
5. 补原始 DTB 的硬件兼容性、完整 eMMC 协议，以及图形 FreeRTOS 真板自主启动验证。
6. 扩展生命周期、端口占用、服务异常及 backing 镜像前后校验的覆盖，并记录会话持久化需求。

以上剩余项按现有实现列出，后续工作需结合用户当前目标推进。
