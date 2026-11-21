"""Temporary test: official kernel + vendor rootfs, without changing base images."""
import json, socket, subprocess, tempfile, time
from pathlib import Path
ROOT=Path('/mnt/d/Workspace/StudyNote/IM6/qemu')
with tempfile.TemporaryDirectory(prefix='im6-linux-test-') as d:
 d=Path(d)
 root_overlay=Path('/tmp/im6-official-local-debug.qcow2')
 if not root_overlay.exists(): subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','raw','-b','/tmp/im6-official-rootfs-bFg0HR/rootfs.ext4',str(root_overlay)],check=True)
 subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','raw','-b',str(ROOT/'images/uboot-emmc.img'),str(d/'emmc.qcow2')],check=True)
 cmd=[str(ROOT/'bin/qemu-system-arm-linux'),'-M','mcimx6ull-alientek','-m','512','-smp','1',
  '-drive',f'if=sd,index=0,format=qcow2,file={root_overlay}',
  '-drive',f'if=sd,index=1,format=qcow2,file={d}/emmc.qcow2',
  '-device',f'loader,file={ROOT}/images/zImage,addr=0x80800000,force-raw=on',
  '-device',f'loader,file={ROOT}/images/board-alientek-full.dtb,addr=0x83000000,force-raw=on',
  '-serial',f'unix:{d}/serial,server=on,wait=on','-qmp',f'unix:{d}/qmp,server=on,wait=off',
  '-nic','user,model=imx.enet','-nic','user,model=imx.enet','-monitor','none','-display','none']
 p=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 output=bytearray(); ser=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
 try:
  for i in range(200):
   try:ser.connect(str(d/'serial'));break
   except OSError:time.sleep(.1)
  ser.settimeout(.5)
  def until(marker, timeout):
   end=time.monotonic()+timeout;data=bytearray()
   while time.monotonic()<end:
    try:chunk=ser.recv(8192)
    except socket.timeout:continue
    if not chunk:break
    data.extend(chunk);output.extend(chunk);print(chunk.decode(errors='replace'),end='',flush=True)
    if b'\x1b[6n' in data: ser.sendall(b'\x1b[30;100R'); data=data.replace(b'\x1b[6n', b'')
    if marker in data:return True
   return False
  if not until(b'=>',60):raise RuntimeError('U-Boot prompt missing')
  for command in ['setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0 rootwait rw','bootz 0x80800000 - 0x83000000']:
   ser.sendall(command.encode()+b'\r')
   if command.startswith('setenv') and not until(b'=>',20): raise RuntimeError('setenv failed')
  until(b'ATK-IMX6U:',150)
  print('等待官方 Qt 界面加载...',flush=True)
  time.sleep(75)
  q=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);q.connect(str(d/'qmp'));f=q.makefile('rwb',buffering=0);f.readline()
  for req in [{'execute':'qmp_capabilities'},{'execute':'screendump','arguments':{'filename':str(ROOT/'runs/official-rootfs-test.ppm')}}]:
   f.write((json.dumps(req)+'\n').encode()); print('QMP',f.readline().decode(),flush=True)
  time.sleep(5)
  until(b'not-a-real-end-marker',15)
 finally:
  (ROOT/'runs/official-rootfs-test.log').write_bytes(output)
  ser.close();p.terminate();p.wait(timeout=5)
