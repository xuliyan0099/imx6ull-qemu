import subprocess, time, os, select, sys, socket, json
root='/mnt/d/Workspace/StudyNote/IM6/qemu'
elf='/mnt/d/Workspace/FreeRTOS/IMX6ULL/build/FreeRTOSIMX6ULL.elf'
q='/tmp/im6-graphics-qemu/qemu-11.1.0/build/qemu-system-arm'
cmd=[q,'-M','mcimx6ull-alientek','-m','512','-smp','1','-watchdog-action','none','-global','arm_gic.num-priority-bits=5','-kernel',elf,'-serial','stdio','-qmp','unix:/tmp/im6-graphics-qmp,server=on,wait=off','-monitor','none','-display','none','-gdb','tcp:127.0.0.1:9321','-no-reboot']
try: os.unlink('/tmp/im6-graphics-qmp')
except FileNotFoundError: pass
p=subprocess.Popen(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
buf=b''; granted=False; end=time.monotonic()+90
try:
 while time.monotonic()<end:
  ready,_,_=select.select([p.stdout],[],[],1)
  if ready:
   chunk=os.read(p.stdout.fileno(),4096)
   if not chunk:break
   sys.stdout.buffer.write(chunk);sys.stdout.buffer.flush();buf+=chunk
  if not granted and ('等待调试器加载'.encode() in buf):
   cmd=['gdb-multiarch','-q','-batch',elf,'-ex','target remote 127.0.0.1:9321','-ex','set var g_ddr_boot_status.load_permission=0x4c4f4144','-ex','detach']
   res=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15)
   print('\nGDB',res.returncode,res.stdout.decode(errors='replace'),flush=True);granted=True
  if b'[lvgl]' in buf:
   time.sleep(5)
   sock=socket.socket(socket.AF_UNIX);sock.connect('/tmp/im6-graphics-qmp'); stream=sock.makefile('rwb', buffering=0); stream.readline()
   for command in ({'execute':'qmp_capabilities'}, {'execute':'input-send-event','arguments':{'events':[{'type':'abs','data':{'axis':'x','value':8000}},{'type':'abs','data':{'axis':'y','value':14000}},{'type':'btn','data':{'button':'left','down':True}}]}}, {'execute':'input-send-event','arguments':{'events':[{'type':'btn','data':{'button':'left','down':False}}]}}, {'execute':'screendump','arguments':{'filename':root+'/experiments/graphics/screen.ppm'}}):
    stream.write((json.dumps(command)+'\n').encode()); print('QMP',stream.readline().decode(),flush=True); time.sleep(1)
   sock.close();break
  if b'initialization failed' in buf or b'[assert]' in buf:break
finally:
 p.terminate();p.wait(timeout=5)
 open('/mnt/d/Workspace/StudyNote/IM6/qemu/experiments/graphics/boot-test.log','wb').write(buf)

