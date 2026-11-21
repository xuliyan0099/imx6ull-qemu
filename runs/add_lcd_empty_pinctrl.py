import subprocess, os
src = '/tmp/min5.dts'
text = open(src).read()

# Empty pinctrl group: valid state, zero pins, so pinctrl driver does not
# program IOMUXC or call udelay before the GPT clocksource is usable.
pwm = text.find('\t\t\t\t\tpwm1grp {', text.find('lcdifctrlgrp'))
if pwm < 0:
    raise SystemExit('pwm1grp anchor not found')
dummy = '''\t\t\t\t\tlcdifemptygrp {
\t\t\t\t\t\tfsl,pins = <>;
\t\t\t\t\t\tlinux,phandle = <0x100>;
\t\t\t\t\t\tphandle = <0x100>;
\t\t\t\t\t};

'''
text = text[:pwm] + dummy + text[pwm:]

start = text.find('lcdif@021c8000')
status = text.find('\t\t\t\tstatus = "okay";', start)
end = status + len('\t\t\t\tstatus = "okay";')
text = text[:end] + '\n\t\t\t\tpinctrl-names = "default";\n\t\t\t\tpinctrl-0 = <0x100>;' + text[end:]

out_dts = '/tmp/board-lcd-empty.dts'
open(out_dts, 'w').write(text)
out_dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-lcd-empty.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',out_dtb,out_dts], capture_output=True, text=True)
print('rc', r.returncode, 'size', os.path.getsize(out_dtb) if os.path.exists(out_dtb) else 0)
if r.returncode:
    print(r.stderr[-2000:])
