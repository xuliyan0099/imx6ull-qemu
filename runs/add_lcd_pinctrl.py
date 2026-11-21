import subprocess, os
src = '/tmp/min5.dts'
text = open(src).read()

# Add back only the LCDIF pinctrl state. The group nodes are still present
# in board-min5.dtb; mxsfb returns -22 if it cannot get a default pinctrl state.
needle = '''\t\t\tlcdif@021c8000 {
\t\t\t\tcompatible = "fsl,imx6ul-lcdif\\0fsl,imx28-lcdif";
\t\t\t\treg = <0x21c8000 0x4000>;
\t\t\t\tinterrupts = <0x00 0x05 0x04>;
\t\t\t\tclocks = <0x01 0xa2 0x01 0xa1 0x01 0x00>;
\t\t\t\tclock-names = "pix\\0axi\\0disp_axi";
\t\t\t\tstatus = "okay";
'''
if needle not in text:
    # dtc indentation may differ; locate node and insert after its status line
    start = text.find('lcdif@021c8000')
    if start < 0:
        raise SystemExit('lcdif node not found')
    status = text.find('\t\t\t\tstatus = "okay";', start)
    if status < 0:
        raise SystemExit('status not found')
    end = status + len('\t\t\t\tstatus = "okay";')
    insert = '\n\t\t\t\tpinctrl-names = "default";\n\t\t\t\tpinctrl-0 = <0x3b 0x3c>;'
    text = text[:end] + insert + text[end:]
else:
    text = text.replace(needle, needle + '\t\t\t\tpinctrl-names = "default";\n\t\t\t\tpinctrl-0 = <0x3b 0x3c>;\n', 1)

out_dts = '/tmp/board-lcd-pinctrl.dts'
open(out_dts, 'w').write(text)
out_dtb = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-lcd-pinctrl.dtb'
r = subprocess.run(['dtc','-I','dts','-O','dtb','-o',out_dtb,out_dts], capture_output=True, text=True)
print('rc', r.returncode, 'size', os.path.getsize(out_dtb) if os.path.exists(out_dtb) else 0)
if r.returncode:
    print(r.stderr[-2000:])
