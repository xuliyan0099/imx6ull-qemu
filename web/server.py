import asyncio, hashlib, json, os, re, secrets, shutil, signal, tempfile
from pathlib import Path
from aiohttp import web, WSMsgType

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / 'web/static'
IMAGE_DIR = Path(os.environ.get('IM6_IMAGE_DIR', str(ROOT / 'images'))).resolve()
FREERTOS_DIR = Path(os.environ.get('IM6_FREERTOS_DIR', '/mnt/d/Workspace/FreeRTOS/IMX6ULL/build')).resolve()

def image_path(name):
    path = IMAGE_DIR / name
    return path if path.is_file() else ROOT / 'images' / name
TOKEN = secrets.token_urlsafe(24)
SERVICE_VERSION = '2026-11-22-official-linux-netui-2'
PORT = int(os.environ.get('IM6_WEB_PORT', '8765'))
BIND_HOST = os.environ.get('IM6_BIND_HOST', '127.0.0.1')
ALLOWED_HOSTS = {item.strip() for item in os.environ.get(
    'IM6_ALLOWED_HOSTS', f'localhost:{PORT},127.0.0.1:{PORT}').split(',') if item.strip()}
ALLOWED_ORIGINS = {f'http://{host}' for host in ALLOWED_HOSTS}
VNC_DISPLAY = int(os.environ.get('IM6_VNC_DISPLAY', '77'))
DISPLAY_MODE = os.environ.get('IM6_DISPLAY', 'vnc')
AUDIO_BACKEND = os.environ.get('IM6_AUDIO_BACKEND', 'wav')
AUDIO_DEVICE = os.environ.get('IM6_AUDIO_DEVICE', 'default')
AUDIO_FILE = Path(os.environ.get('IM6_AUDIO_FILE', str(ROOT / 'runs' / 'audio.wav'))).resolve()

class Board:
    def __init__(self):
        self.proc = None; self.work = None; self.serial = None; self.qmp = None
        self.history = bytearray(); self.clients = set(); self.state = 'stopped'; self.lock = asyncio.Lock()
        self.profile = None; self.boot_task = None; self.error = ''; self.boot_state = 'idle'; self.boot_message = ''; self.boot_queue = None; self.led_state = None; self.led_task = None; self.serial_tail = b''

    async def connect_unix(self, name):
        for _ in range(150):
            if self.proc.returncode is not None: raise RuntimeError('QEMU 已退出，请检查运行日志')
            try: return await asyncio.open_unix_connection(str(self.work / name))
            except (FileNotFoundError, ConnectionRefusedError): await asyncio.sleep(.1)
        raise RuntimeError(name + ' 连接超时')

    async def command(self, command, arguments=None):
        if not self.qmp: raise RuntimeError('QMP 尚未连接')
        async with self.lock:
            reader, writer = self.qmp
            request = {'execute': command}
            if arguments is not None: request['arguments'] = arguments
            writer.write((json.dumps(request) + '\n').encode()); await writer.drain()
            while True:
                response = json.loads(await asyncio.wait_for(reader.readline(), 5))
                if 'error' in response: raise RuntimeError(str(response['error']))
                if 'return' in response: return response['return']

    async def start(self, profile):
        if self.state not in ('stopped', 'error'): raise RuntimeError('已有运行中的会话')
        if profile not in ('linux', 'linux-official', 'freertos', 'freertos-gui', 'freertos-gui-emmc'): raise ValueError('无效启动配置')
        self.state = 'starting'; self.error = ''; self.profile = profile; self.history.clear()
        self.work = Path(tempfile.mkdtemp(prefix='im6-board-'))
        try:
            image = image_path('uboot-emmc.img' if profile in ('linux', 'linux-official') else 'emmc-uboot-freertos.img')
            overlay = self.work / 'emmc.qcow2'
            maker = await asyncio.create_subprocess_exec('qemu-img','create','-q','-f','qcow2','-F','raw','-b',str(image),str(overlay),stderr=asyncio.subprocess.PIPE)
            _, err = await maker.communicate()
            if maker.returncode: raise RuntimeError('创建 overlay 失败: ' + err.decode(errors='replace'))
            if profile == 'linux':
                fat = self.work / 'fat'; fat.mkdir()
                for name, target in [('zImage','zimage-official'),('board-alientek-full.dtb','board-alientek-full.dtb'),('ramdisk.uimg','ramdisk.uimg')]: shutil.copyfile(image_path(name), fat / target)
                sd = 'fat:rw:' + str(fat)
                sd_format = 'raw'
            elif profile == 'linux-official':
                sd = str(self.work / 'official-rootfs.qcow2'); sd_format = 'qcow2'
                base = image_path('official-rootfs.ext4')
                if not base.is_file(): raise RuntimeError('缺少出厂根文件系统镜像；请先运行 scripts/build-official-rootfs.sh')
                maker = await asyncio.create_subprocess_exec('qemu-img','create','-q','-f','qcow2','-F','raw','-b',str(base),sd,stderr=asyncio.subprocess.PIPE)
                _, err = await maker.communicate()
                if maker.returncode: raise RuntimeError('创建根文件系统 overlay 失败: ' + err.decode(errors='replace'))
            else:
                tf = self.work / 'tf.qcow2'
                maker = await asyncio.create_subprocess_exec('qemu-img','create','-q','-f','qcow2','-F','raw','-b',str(image_path('tf.img')),str(tf))
                if await maker.wait(): raise RuntimeError('创建 TF overlay 失败')
                sd = str(tf); sd_format = 'qcow2'
            qemu_binary = {
                'linux-official': 'bin/qemu-system-arm-official-linux',
                'freertos-gui': 'bin/qemu-system-arm-graphics-linux',
                'freertos-gui-emmc': 'bin/qemu-system-arm-graphics-linux',
            }.get(profile, 'bin/qemu-system-arm-linux')
            sd_cache = '' if sd.startswith('fat:rw:') else ',cache=unsafe'
            display_args = (['-display','gtk,grab-on-hover=off'] if DISPLAY_MODE == 'gtk'
                            else ['-display','none','-vnc',f'127.0.0.1:{VNC_DISPLAY},lossy=on'])
            args = [str(ROOT/qemu_binary),'-accel','tcg,thread=multi,tb-size=512','-M','mcimx6ull-alientek','-m','512','-smp','1', '-drive',f'if=sd,index=0,format={sd_format},file={sd}{sd_cache}', '-drive',f'if=sd,index=1,format=qcow2,file={overlay},cache=unsafe', '-qmp',f'unix:{self.work}/qmp,server=on,wait=off','-serial',f'unix:{self.work}/serial,server=on,wait=on','-L','/usr/share/qemu',*display_args,'-monitor','none']
            if profile == 'linux-official':
                args += ['-device',f'loader,file={image_path("zImage")},addr=0x80800000,force-raw=on','-device',f'loader,file={image_path("board-alientek-official-gui.dtb")},addr=0x83000000,force-raw=on']
            if profile in ('linux', 'linux-official'):
                AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
                if AUDIO_BACKEND == 'wav':
                    audio_spec = f'wav,id=im6snd,path={AUDIO_FILE}'
                elif AUDIO_BACKEND == 'alsa':
                    audio_spec = f'alsa,id=im6snd,dev={AUDIO_DEVICE}'
                else:
                    audio_spec = 'none,id=im6snd'
                args += ['-audiodev', audio_spec,
                         '-device', 'usb-audio,bus=usb-bus.0,audiodev=im6snd']
            if profile in ('freertos', 'freertos-gui', 'freertos-gui-emmc'): args += ['-watchdog-action','none']
            else: args += ['-nic','user,model=imx.enet','-nic','user,model=imx.enet']
            if profile in ('freertos-gui', 'freertos-gui-emmc'):
                elf = FREERTOS_DIR / 'FreeRTOSIMX6ULL.elf'
                app = elf.with_name('FreeRTOSIMX6ULL-app.bin')
                manifest = json.loads(elf.with_name('FreeRTOSIMX6ULL-images.json').read_text())
                if hashlib.sha256(elf.read_bytes()).hexdigest() != manifest['sha256'][elf.name]:
                    raise RuntimeError('真机 ELF 校验不匹配，请重新构建')
                if not app.is_file(): raise RuntimeError('缺少 DDR 应用 bin')
                args += ['-global','arm_gic.num-priority-bits=5','-gdb',f'unix:{self.work}/gdb,server=on,wait=off']
                if profile == 'freertos-gui': args += ['-kernel',str(elf)]
                else:
                    self.image_blocks = {}
                    for kind, offset in (('boot',0x100000),('app',0x200000)):
                        binary = elf.with_name(f'FreeRTOSIMX6ULL-{kind}.bin')
                        section = elf.with_name(f'FreeRTOSIMX6ULL-{kind}.elf')
                        if hashlib.sha256(section.read_bytes()).hexdigest() != manifest['sha256'][section.name]: raise RuntimeError(kind+' ELF 校验不匹配')
                        verified = self.work/(kind+'-verified.bin')
                        proc = await asyncio.create_subprocess_exec('arm-none-eabi-objcopy','-O','binary',str(section),str(verified),stderr=asyncio.subprocess.PIPE)
                        _, error = await proc.communicate()
                        if proc.returncode or hashlib.sha256(verified.read_bytes()).digest() != hashlib.sha256(binary.read_bytes()).digest(): raise RuntimeError(kind+' 二进制与 ELF 不匹配')
                        contents = binary.read_bytes(); blocks = (len(contents)+511)//512
                        if kind == 'boot' and blocks * 512 > 0x100000: raise RuntimeError('引导段超出区域')
                        padded = self.work/(kind+'-padded.bin'); padded.write_bytes(contents.ljust(blocks*512,b'\x00'))
                        proc = await asyncio.create_subprocess_exec('qemu-io','-f','qcow2','-c',f'write -q -s {padded} {offset} {blocks*512}',str(overlay),stderr=asyncio.subprocess.PIPE)
                        _, error = await proc.communicate()
                        if proc.returncode: raise RuntimeError('写入临时 eMMC 失败: '+error.decode(errors='replace'))
                        self.image_blocks[kind] = blocks
            log = open(self.work/'qemu.log','wb')
            self.proc = await asyncio.create_subprocess_exec(*args, cwd=str(ROOT), stdout=log, stderr=log); log.close()
            self.serial = await self.connect_unix('serial')
            self.qmp = await self.connect_unix('qmp')
            await self.qmp[0].readline(); await self.command('qmp_capabilities')
            self.state = 'running'
            self.begin_boot()
            asyncio.create_task(self.read_serial()); asyncio.create_task(self.watch()); self.led_task = asyncio.create_task(self.poll_led())
        except Exception as e:
            logtext = (self.work/'qemu.log').read_text(errors='replace')[-2000:] if self.work and (self.work/'qemu.log').exists() else ''
            self.error = str(e) + ' ' + logtext; await self.stop(); self.state = 'error'; raise RuntimeError(self.error)

    async def read_serial(self):
        reader, _ = self.serial
        try:
            while data := await reader.read(4096):
                self.history.extend(data)
                if self.profile == 'linux-official':
                    scan = self.serial_tail + data
                    if b'\x1b[6n' in scan and self.serial:
                        self.serial[1].write(b'\x1b[30;100R'); await self.serial[1].drain()
                    self.serial_tail = scan[-3:]
                if self.boot_queue is not None: self.boot_queue.put_nowait(data)
                if len(self.history) > 131072: del self.history[:-131072]
                for client in list(self.clients):
                    try: await client.send_bytes(data)
                    except Exception: self.clients.discard(client)
        except (ConnectionError, asyncio.CancelledError): pass

    def begin_boot(self):
        if self.boot_task and not self.boot_task.done(): self.boot_task.cancel()
        self.boot_queue = asyncio.Queue()
        self.boot_state = 'booting'; self.boot_message = '等待 U-Boot'
        self.boot_task = asyncio.create_task(self.auto_boot(self.boot_queue, self.profile))

    async def auto_boot(self, queue, profile):
        buffer = bytearray()
        async def until(marker, timeout):
            async def receive():
                while marker not in buffer:
                    if len(buffer) > 262144: raise RuntimeError('串口输出超过引导缓冲区')
                    buffer.extend(await queue.get())
                pos = buffer.index(marker) + len(marker)
                result = bytes(buffer[:pos]); del buffer[:pos]
                return result
            return await asyncio.wait_for(receive(), timeout)
        async def send(line):
            self.serial[1].write(line.encode() + b'\r'); await self.serial[1].drain()
        try:
            if profile in ('freertos-gui', 'freertos-gui-emmc'):
                if profile == 'freertos-gui-emmc':
                    await until(b'=>', 60)
                    steps = [('mmc dev 1', None),
                             (f'mmc read 0x900000 0x800 {self.image_blocks["boot"]:x}', f'{self.image_blocks["boot"]} blocks read: OK'.encode()),
                             (f'mmc read 0x80000000 0x1000 {self.image_blocks["app"]:x}', f'{self.image_blocks["app"]} blocks read: OK'.encode())]
                    for line, expected in steps:
                        self.boot_message = line; await send(line); output = await until(b'=>', 60)
                        if expected and expected not in output: raise RuntimeError('eMMC 装载失败: '+line)
                    await send('go 0x900020')
                await until('等待调试器加载'.encode(), 60)
                self.boot_message = '验证 DDR 镜像'
                elf = str(FREERTOS_DIR / 'FreeRTOSIMX6ULL.elf')
                app = FREERTOS_DIR / 'FreeRTOSIMX6ULL-app.bin'
                dumped = self.work / 'ddr-app.bin'
                end = 0x80000000 + app.stat().st_size
                async def gdb(*commands):
                    args = ['gdb-multiarch','-q','-batch',elf,'-ex',f'target remote {self.work}/gdb']
                    for cmd in commands: args += ['-ex',cmd]
                    args += ['-ex','detach']
                    process = await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
                    output, _ = await asyncio.wait_for(process.communicate(), 20)
                    if process.returncode: raise RuntimeError('GDB 访问失败: '+output.decode(errors='replace')[-500:])
                commands = [f'dump binary memory {dumped} 0x80000000 {end:#x}']
                bootbin = app.with_name('FreeRTOSIMX6ULL-boot.bin')
                bootdump = self.work / 'ocram-boot.bin'
                if profile == 'freertos-gui-emmc': commands.append(f'dump binary memory {bootdump} 0x900000 {0x900000 + bootbin.stat().st_size:#x}')
                await gdb(*commands)
                if profile == 'freertos-gui-emmc' and hashlib.sha256(bootdump.read_bytes()).digest() != hashlib.sha256(bootbin.read_bytes()).digest(): raise RuntimeError('OCRAM 引导段校验不通过，未授予启动许可')
                if hashlib.sha256(dumped.read_bytes()).digest() != hashlib.sha256(app.read_bytes()).digest():
                    raise RuntimeError('DDR 应用校验不通过，未授予启动许可')
                await gdb('set var g_ddr_boot_status.load_permission=0x4c4f4144')
                self.boot_message = '等待 LVGL 启动'
                await until(b'[lvgl] 9.2.2', 120)
                self.boot_state = 'ready'; self.boot_message = 'FreeRTOS 图形版已启动；GT1158 触摸为实验模型'
                return
            await until(b'=>', 60)
            if profile == 'linux-official':
                self.boot_message = '启动出厂 Linux 内核和文件系统'
                await send('setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0 rootwait rw')
                await until(b'=>', 30)
                await send('bootz 0x80800000 - 0x83000000')
                self.boot_message = '出厂 Linux 正在初始化，首次启动可能需要数分钟'
                await until(b'~# ', 240)
                self.boot_state = 'ready'
                self.boot_message = '出厂 Linux 已启动，原厂启动脚本正在加载桌面'
                return
            if profile == 'linux':
                steps = [
                    ('mmc dev 0', None),
                    ('fatload mmc 0:1 0x80800000 zimage-official', b'bytes read'),
                    ('fatload mmc 0:1 0x83000000 board-alientek-full.dtb', b'bytes read'),
                    ('fatload mmc 0:1 0x84000000 ramdisk.uimg', b'bytes read'),
                    ('setenv bootargs console=ttymxc0,115200 root=/dev/ram0 rw', None),
                ]
                final = 'bootz 0x80800000 0x84000000 0x83000000'; marker = b'IMX6ULL QEMU initramfs shell'
            else:
                steps = [('mmc dev 1', None), ('mmc read 0x900000 0x800 0x20', b'32 blocks read: OK')]
                final = 'go 0x900020'; marker = b'FreeRTOS V11.3.1'
            for line, expected in steps:
                self.boot_message = line
                await send(line); output = await until(b'=>', 60)
                if expected and expected not in output: raise RuntimeError('引导命令失败: ' + line)
                if any(error in output for error in (b'** Unable', b'No such device', b'Error reading')): raise RuntimeError('引导命令失败: ' + line)
            self.boot_message = final
            await send(final); await until(marker, 120)
            self.boot_state = 'ready'; self.boot_message = '系统已启动'
        except asyncio.CancelledError:
            raise
        except (Exception, asyncio.TimeoutError) as exc:
            self.boot_state = 'manual'; self.boot_message = f'自动引导停止：{str(exc) or "等待超时"}；可使用串口手动操作'
        finally:
            if self.boot_queue is queue: self.boot_queue = None

    def network(self):
        text = bytes(self.history)
        link0 = b'eth0: Link is Up' in text
        link1 = b'eth1: Link is Up' in text
        speed = '100Mbps/Full' if b'100Mbps/Full' in text else ''
        return {
            'physical': {'port':'ENET2','soc':'FEC2','iface':'eth1',
                         'phy':'LAN8720A / SR8201F','phy_addr':'0x1','mode':'RMII',
                         'connector':'RJ45 · 内置隔离变压器'},
            'soc_only': {'soc':'FEC1','iface':'eth0','wired':False},
            'link': {'eth1': link1, 'eth0': link0},
            'guest_ip': '10.0.2.15' if link1 else '',
            'gateway': '10.0.2.2',
            'speed': speed,
            'nat': True,
        }

    async def poll_led(self):
        try:
            while self.proc and self.proc.returncode is None:
                try:
                    output = await self.command('human-monitor-command', {'command-line':'xp /2wx 0x0209c000'})
                    values = re.findall(r'0x[0-9a-fA-F]+', output)
                    if len(values) != 2: raise ValueError('GPIO 格式错误')
                    data, direction = int(values[-2], 16), int(values[-1], 16)
                    self.led_state = (not bool(data & 8)) if direction & 8 else None
                except (ValueError, RuntimeError, asyncio.TimeoutError, ConnectionError):
                    self.led_state = None
                await asyncio.sleep(.5)
        except asyncio.CancelledError:
            pass
        finally:
            self.led_state = None

    async def watch(self):
        proc = self.proc; code = await proc.wait()
        if self.proc is proc and self.state not in ('stopping','stopped'):
            log = (self.work/'qemu.log').read_text(errors='replace')[-2000:]
            self.error = f'QEMU 已退出 ({code})：{log}'; self.state = 'error'

    async def stop(self):
        self.state = 'stopping'
        if self.led_task:
            self.led_task.cancel(); await self.led_task; self.led_task = None
        self.led_state = None
        if self.boot_task and not self.boot_task.done():
            self.boot_task.cancel()
            try: await self.boot_task
            except asyncio.CancelledError: pass
        self.boot_task = None; self.boot_queue = None; self.boot_state = 'idle'; self.boot_message = ''
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try: await asyncio.wait_for(self.proc.wait(),5)
            except asyncio.TimeoutError: self.proc.kill(); await self.proc.wait()
        for pair in (self.serial,self.qmp):
            if pair: pair[1].close()
        self.serial = self.qmp = self.proc = None
        if self.work: shutil.rmtree(self.work,ignore_errors=True); self.work = None
        self.state = 'stopped'

board = Board()
@web.middleware
async def guard(request, handler):
    if request.host not in ALLOWED_HOSTS: raise web.HTTPForbidden()
    origin = request.headers.get('Origin')
    if origin and origin not in ALLOWED_ORIGINS: raise web.HTTPForbidden()
    if request.path.startswith('/api') or request.path.startswith('/ws'):
        if request.query.get('token') != TOKEN and request.headers.get('X-Token') != TOKEN: raise web.HTTPForbidden()
    return await handler(request)

async def index(request): return web.FileResponse(STATIC/'index.html')
async def token(request): return web.json_response({'token':TOKEN})
async def version(request): return web.json_response({'service':'im6-virtual-board','version':SERVICE_VERSION,'launch_id':os.environ.get('IM6_LAUNCH_ID',''),'display':DISPLAY_MODE,'audio':AUDIO_BACKEND})
async def audio(request):
    if not AUDIO_FILE.is_file(): raise web.HTTPNotFound()
    return web.FileResponse(AUDIO_FILE, headers={'Cache-Control':'no-store'})
async def status(request): return web.json_response({'state':board.state,'profile':board.profile,'error':board.error,'boot_state':board.boot_state,'boot_message':board.boot_message,'led':board.led_state,'net':board.network()})
async def serial_text(request): return web.json_response({'text':bytes(board.history).decode(errors='replace')[-12000:]})
async def action(request):
    try:
        action = request.match_info['action']
        if action == 'start': await board.start((await request.json()).get('profile'))
        elif action == 'stop': await board.stop()
        elif action == 'manual':
            if board.boot_state != 'booting': raise RuntimeError('当前没有自动引导任务')
            board.boot_task.cancel(); board.boot_state = 'manual'; board.boot_message = '已切换到手动串口操作'
        elif action in ('pause','resume','reset'):
            if board.state not in ('running','paused'): raise RuntimeError('开发板未运行')
            if action == 'pause' and board.boot_state == 'booting': raise RuntimeError('自动引导期间请先等待或手动接管')
            if action == 'reset' and board.state == 'paused': raise RuntimeError('请先继续运行，再复位')
            if action == 'reset': board.begin_boot()
            try:
                await board.command({'pause':'stop','resume':'cont','reset':'system_reset'}[action])
            except Exception:
                if action == 'reset' and board.boot_task: board.boot_task.cancel(); board.boot_state = 'manual'; board.boot_message = '复位失败，可手动操作串口'
                raise
            if action != 'reset': board.state = 'paused' if action == 'pause' else 'running'
        else: raise web.HTTPNotFound()
        return await status(request)
    except web.HTTPException: raise
    except Exception as e: return web.json_response({'error':str(e)},status=400)

async def serial_ws(request):
    ws = web.WebSocketResponse(); await ws.prepare(request); board.clients.add(ws)
    if board.history: await ws.send_bytes(bytes(board.history))
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT and board.serial and board.boot_state != 'booting':
                board.serial[1].write(msg.data.encode()); await board.serial[1].drain()
    finally: board.clients.discard(ws)
    return ws

async def vnc_ws(request):
    ws = web.WebSocketResponse(protocols=('binary',)); await ws.prepare(request)
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1',5900 + VNC_DISPLAY)
        async def forward():
            while data := await reader.read(65536): await ws.send_bytes(data)
        task = asyncio.create_task(forward())
        async for msg in ws:
            if msg.type == WSMsgType.BINARY: writer.write(msg.data); await writer.drain()
        task.cancel(); writer.close(); await writer.wait_closed()
    except (OSError, ConnectionError): pass
    return ws

async def cleanup(app): await board.stop()
app = web.Application(middlewares=[guard]); app.router.add_get('/',index); app.router.add_get('/token',token); app.router.add_get('/version',version); app.router.add_get('/api/status',status); app.router.add_get('/api/serial',serial_text); app.router.add_post('/api/{action}',action); app.router.add_get('/ws/serial',serial_ws); app.router.add_get('/ws/vnc',vnc_ws); app.router.add_get('/audio.wav',audio); app.router.add_static('/static/',STATIC); app.on_cleanup.append(cleanup)
if __name__ == '__main__':
    web.run_app(app,host=BIND_HOST,port=PORT,print=lambda s: print(s,flush=True))








