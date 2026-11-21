import subprocess, os
src = '/tmp/min5.dts'
text = open(src).read()

# Use pinctrl-single as a harmless provider for mxsfb.  The vendor
# imx6ul-pinctrl driver is blacklisted; it calls udelay before the GPT
# clocksource is available and hangs.  pinctrl-single only programs one
# dummy pad register and does not delay.
node = '''
\tpinctrl_single: pinctrl-single@020e0000 {
\t\tcompatible = "pinctrl-single";
\t\treg = <0x020e0000 0x700>;
\t\tpinctrl-single,register-width = <32>;
\t\tpinctrl-single,function-mask = <0xffffffff>;
\t\tstatus = "okay";

\t\tlcdifdummy: lcdifdummy {
\t\t\tpinctrl-single,pins = <0x118 0x00>;
\t\t\tlinux,phandle = <0x100>;
\t\t\tphandle = <0x100>;
\t\t};
\t};
'''
# insert inside root node, just before memory
mem = text.find('\tmemory {')
if mem < 0:
    raise SystemExit('memory node not found')
text = text[:mem] + node + '\n' + text[mem:]

# lcdif gets the pinctrl-single state
start = text.find('lcdif@021c8000')
status = text.find('\t\t\t\tstatus = "okay";', start)
end = status + len('\t\t\t\tstatus = "okay";')
text = text[:end] + '\n\t\t\t\tpinctrl-names = "default";\n\t\t\t\tpinctrl-0 = <0x100>;' + text[end:]

out_dts = '/tmp/board-lcd-single.dts'
open(out_dts, 'w').write(text)
out_dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-lcd-single.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',out_dtb,out_dts], capture_output=True, text=True)
print('rc', r.returncode, 'size', os.path.getsize(out_dtb) if os.path.exists(out_dtb) else 0)
if r.returncode:
    print(r.stderr[-2000:])
