"""Run against an already-started local web/server.py; leaves no QEMU running."""
import json, time, urllib.request
BASE = 'http://127.0.0.1:8765/'
token = json.load(urllib.request.urlopen(BASE + 'token'))['token']
def api(path, payload=None):
    request = urllib.request.Request(BASE+'api/'+path, data=json.dumps(payload).encode() if payload is not None else None, headers={'X-Token':token,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(request, timeout=60))
def wait_ready():
    end = time.monotonic()+90
    while time.monotonic()<end:
        state=api('status')
        if state['boot_state']=='ready': return
        if state['boot_state']=='manual' or state['state']=='error': raise RuntimeError(str(state))
        time.sleep(.25)
    raise TimeoutError('boot')
try:
    api('start',{'profile':'freertos'}); wait_ready()
    samples=[]
    for _ in range(20): samples.append(api('status')['led']); time.sleep(.15)
    assert True in samples and False in samples, samples
    api('reset',{}); wait_ready()
    print('PASS FreeRTOS automatic boot, sampled DS0, reset and automatic reboot')
finally:
    api('stop',{})
