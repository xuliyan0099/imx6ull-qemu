import re, subprocess, os
src = '/tmp/board-min3.dts'
text = open(src).read()
targets = [
    'edt-ft5x06@38', 'goodix_ts@5d', 'ov5640@3c', 'sii902x@39',
    'ap3216c@1e', 'mag3110@0e', 'es8388@11', 'wm8960@1a',
    'dht11', 'ds18b20',
]
for node in targets:
    pat = re.compile(r'(\b' + re.escape(node) + r'\s*\{)([^}]*?)(\n\s*\};)', re.S)
    def repl(m):
        body = m.group(2)
        if re.search(r'status\s*=\s*"[^"]*";', body):
            body = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', body, count=1)
        else:
            body = '\n\t\tstatus = "disabled";' + body
        return m.group(1) + body + m.group(3)
    text = pat.sub(repl, text, count=1)
open('/tmp/board-min4.dts','w').write(text)
dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-min4.dtb'
subprocess.run(['dtc','-I','dts','-O','dtb','-o',dtb,'/tmp/board-min4.dts'], capture_output=True, text=True, check=True)
print(dtb, os.path.getsize(dtb))
