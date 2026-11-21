import subprocess, os
src = '/tmp/min5.dts'
text = open(src).read()

# Add a single dummy pin pinctrl group and point LCDIF at it.  The real
# lcdif groups program many IOMUXC registers; if QEMU's unimplemented
# iomuxc rejects those writes the kernel stalls before UART comes up.
# A one-entry group is enough to satisfy mxsfb's pinctrl_lookup_state().
anchor = '''\t\t\t\t\tlcdifctrlgrp {
'''
if anchor not in text:
    raise SystemExit('lcdifctrlgrp anchor not found')
# insert after the closing brace of lcdifctrlgrp, before pwm1grp
pwm = text.find('\t\t\t\t\tpwm1grp {', text.find('lcdifctrlgrp'))
if pwm < 0:
    raise SystemExit('pwm1grp anchor not found')
dummy = '''\t\t\t\t\tlcdifdummygrp {
\t\t\t\t\t\tfsl,pins = <0x118 0x3a4 0x00 0x00 0x00 0x79>;
\t\t\t\t\t\tlinux,phandle = <0x100>;
\t\t\t\t\t\tphandle = <0x100>;
\t\t\t\t\t};

'''
text = text[:pwm] + dummy + text[pwm:]

# point lcdif at the dummy group
start = text.find('lcdif@021c8000')
status = text.find('\t\t\t\tstatus = "okay";', start)
end = status + len('\t\t\t\tstatus = "okay";')
text = text[:end] + '\n\t\t\t\tpinctrl-names = "default";\n\t\t\t\tpinctrl-0 = <0x100>;' + text[end:]

out_dts = '/tmp/board-lcd-dummy.dts'
open(out_dts, 'w').write(text)
out_dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-lcd-dummy.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',out_dtb,out_dts], capture_output=True, text=True)
print('rc', r.returncode, 'size', os.path.getsize(out_dtb) if os.path.exists(out_dtb) else 0)
if r.returncode:
    print(r.stderr[-2000:])
