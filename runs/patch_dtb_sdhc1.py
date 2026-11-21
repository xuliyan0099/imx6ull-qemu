import re, subprocess, os
src = '/tmp/board-min2.dts'
text = open(src).read()
for node in ['usdhc@02190000']:
    pat = re.compile(r'(\b' + re.escape(node) + r'\s*\{)([^}]*?)(\n\s*\};)', re.S)
    def repl(m):
        body = m.group(2)
        if re.search(r'status\s*=\s*"[^"]*";', body):
            body = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', body, count=1)
        else:
            body = '\n\t\tstatus = "disabled";' + body
        return m.group(1) + body + m.group(3)
    text = pat.sub(repl, text, count=1)
open('/tmp/board-min3.dts','w').write(text)
dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-min3.dtb'
subprocess.run(['dtc','-I','dts','-O','dtb','-o',dtb,'/tmp/board-min3.dts'], check=True)
print(dtb, os.path.getsize(dtb))
