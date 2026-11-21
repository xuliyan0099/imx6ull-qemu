import re, subprocess, os
src = '/tmp/board-all-disabled.dts'
text = open(src).read()
for node in ['busfreq', 'pmu']:
    pat = re.compile(r'(\b' + node + r'\s*\{)([^}]*?)(\n\s*\};)', re.S)
    def repl(m):
        body = m.group(2)
        if re.search(r'status\s*=\s*"[^"]*";', body):
            body = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', body, count=1)
        else:
            body = '\n\t\tstatus = "disabled";' + body
        return m.group(1) + body + m.group(3)
    text = pat.sub(repl, text, count=1)
out = '/tmp/board-min2.dts'
open(out, 'w').write(text)
dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-min2.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',dtb,out], capture_output=True, text=True)
print('dtc rc', r.returncode, 'out', dtb, os.path.getsize(dtb))
print('busfreq status disabled:', 'status = "disabled";' in text.split('busfreq',1)[1].split('};',1)[0])
