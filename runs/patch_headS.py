import re
p = '/tmp/linux-imx/arch/arm/boot/compressed/head.S'
t = open(p).read()
t = t.replace('.section ".start", #alloc, #execinstr', '.section ".start", "ax"')
open(p, 'w').write(t)
print('patched head.S section')
