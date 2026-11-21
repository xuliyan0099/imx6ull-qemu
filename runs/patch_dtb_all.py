import re, subprocess, os
src = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/imx6ull-14x14-emmc-7-800x480-c.dtb'
dts = '/tmp/board-all.dts'
out = '/mnt/d/Workspace/StudyNote/IM6/qemu/images/board-nopinctrl-all.dtb'
subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', '-o', dts, src], check=True)
text = open(dts).read()
# remove all pinctrl-* property assignments (including multi-line)
text2 = re.sub(r'\n\s*pinctrl(?:-[0-9]+|-names)\s*=\s*(?:<[^;]*>|[^;]*);', '', text)
# remove pinctrl-names separately in case value is string list
text2 = re.sub(r'\n\s*pinctrl-names\s*=\s*[^;]*;', '', text2)
open('/tmp/board-all-nopinctrl.dts','w').write(text2)
subprocess.run(['dtc', '-I', 'dts', '-O', 'dtb', '-o', out, '/tmp/board-all-nopinctrl.dts'], check=True)
print('removed props:', len(re.findall(r'pinctrl', text)) - len(re.findall(r'pinctrl', text2)))
print(out, os.path.getsize(out))
