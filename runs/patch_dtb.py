import re
p = '/tmp/board.dts'
out = '/tmp/board-nopinctrl.dts'
s = open(p).read()
m = re.search(r'(serial@02020000 \{.*?\n\t*\};\n)', s, re.S)
if not m:
    raise SystemExit('serial node not found')
block = m.group(1)
new = re.sub(r'\n\t*pinctrl-names = .*?;', '', block)
new = re.sub(r'\n\t*pinctrl-0 = .*?;', '', new)
s = s.replace(block, new)
open(out, 'w').write(s)
print('patched serial node')
