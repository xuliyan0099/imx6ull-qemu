import re, subprocess, os
dts = '/tmp/board-all-nopinctrl.dts'
text = open(dts).read()

targets = [
    'rngb@02284000', 'dcp@02280000', 'epdc@0228c000',
    'csi@021c4000', 'pxp@021cc000', 'qspi@021e0000',
    'gpmi-nand@01806000', 'dma-apbh@01804000', 'sdma@020ec000',
    'adc@02198000', 'tempmon',
    'usb@02184000', 'usb@02184200', 'usbmisc@02184800',
    'ecspi@02008000', 'ecspi@0200c000', 'ecspi@02010000', 'ecspi@02014000',
    'sai@02028000', 'sai@0202c000', 'sai@02030000', 'esai@02024000',
    'spdif@02004000', 'asrc@02034000',
    'can@02090000', 'can@02094000',
    'pwm@02080000', 'pwm@02084000', 'pwm@02088000', 'pwm@0208c000',
    'pwm@020f0000', 'pwm@020f4000', 'pwm@020f8000', 'pwm@020fc000',
    'tsc@02040000',
    'wdog@020bc000', 'wdog@020c0000',
]

for node in targets:
    pat = re.compile(r'(' + re.escape(node) + r'\s*\{)([^}]*?)(\n\s*\};)', re.S)
    def repl(m):
        body = m.group(2)
        if re.search(r'status\s*=\s*"[^"]*";', body):
            body = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', body, count=1)
        else:
            body = '\n\t\tstatus = "disabled";' + body
        return m.group(1) + body + m.group(3)
    text = pat.sub(repl, text, count=1)

open('/tmp/board-all-disabled.dts','w').write(text)
out = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-min.dtb'
subprocess.run(['dtc', '-I','dts','-O','dtb','-o',out,'/tmp/board-all-disabled.dts'], check=True)
print(out, os.path.getsize(out))
