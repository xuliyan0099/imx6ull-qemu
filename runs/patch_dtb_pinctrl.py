import re, subprocess, os
src = '/tmp/board.dts'
text = open(src).read()

# Disable peripherals QEMU does not model. Keep pinctrl properties intact
# so mxsfb can get its default pinctrl state.
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
    'busfreq', 'pmu', 'usdhc@02190000',
    'edt-ft5x06@38', 'goodix_ts@5d',
]

for node in targets:
    start = text.find(node)
    if start < 0:
        print('not found', node)
        continue
    brace = text.find('{', start)
    # nodes with child nodes need a brace-depth scan; simple nodes end at first '\n\t...};'
    depth = 0
    i = brace
    end = -1
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                # include trailing semicolon
                end = text.find(';', i)
                if end >= 0:
                    end += 1
                break
        i += 1
    if end < 0:
        print('end not found', node)
        continue
    block = text[brace:end]
    if re.search(r'status\s*=\s*"[^"]*";', block):
        block = re.sub(r'status\s*=\s*"[^"]*";', 'status = "disabled";', block, count=1)
    else:
        block = '\n\t\t\t\tstatus = "disabled";' + block
    text = text[:brace] + block + text[end:]

out_dts = '/tmp/board-pinctrl.dts'
open(out_dts, 'w').write(text)
out_dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-pinctrl.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',out_dtb,out_dts], capture_output=True, text=True)
print('rc', r.returncode, 'size', os.path.getsize(out_dtb))
if r.returncode:
    print(r.stderr[-2000:])
