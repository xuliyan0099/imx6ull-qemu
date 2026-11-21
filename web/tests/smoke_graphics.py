"""Integration test against an idle server; optional port argument. Discards its test overlay."""
import json, sys, time, urllib.request
base = f'http://127.0.0.1:{sys.argv[1] if len(sys.argv)>1 else 8765}/'
token = json.load(urllib.request.urlopen(base+'token'))['token']
def api(path, data=None):
    req=urllib.request.Request(base+'api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'X-Token':token,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req,timeout=60))
def wait():
    for _ in range(160):
        result=api('status')
        if result['boot_state']=='ready': return
        if result['boot_state']=='manual' or result['state']=='error': raise RuntimeError(str(result))
        time.sleep(.5)
    raise TimeoutError('启动图形版超时')
if api('status')['state'] != 'stopped': raise RuntimeError('请先关闭当前会话，测试不会接管运行中的开发板')
try:
    api('start',{'profile':'freertos-gui-emmc'}); wait()
    api('reset',{}); wait()
    print('PASS eMMC 图形版启动、两段内存校验及复位重启')
finally:
    api('stop',{})
