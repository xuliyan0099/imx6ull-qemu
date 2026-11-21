import re, subprocess, os
src = '/tmp/board-min3.dts'
text = open(src).read()
targets = ['edt-ft5x06@38', 'goodix_ts@5d']
for node in targets:
    start = text.find(node)
    if start < 0:
        print('not found', node); continue
    brace = text.find('{', start)
    end = text.find('\n\t\t\t};', brace)
    if end < 0:
        print('end not found', node); continue
    block = text[brace:end]
    if re.search(r'status\s*=\s*"[^"]*";', block):
        block = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', block, count=1)
    else:
        block = '\n\t\t\t\tstatus = "disabled";' + block
    text = text[:brace] + block + text[end:]
open('/tmp/board-min5.dts','w').write(text)
dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-min5.dtb'
subprocess.run(['dtc','-I','dts','-O','dtb','-o',dtb,'/tmp/board-min5.dts'], capture_output=True, text=True, check=True)
print(dtb, os.path.getsize(dtb))
