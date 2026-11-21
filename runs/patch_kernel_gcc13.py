import re
p = '/tmp/linux-imx/include/linux/log2.h'
t = open(p).read()
t = t.replace('extern __attribute__((const, noreturn))\nint ____ilog2_NaN(void);',
              'extern __attribute__((const))\nint ____ilog2_NaN(void);', 1)
open(p, 'w').write(t)

p = '/tmp/linux-imx/arch/arm/mm/proc-v7.S'
t = open(p).read()
t = t.replace('.section ".proc.info.init", #alloc',
              '.section ".proc.info.init", "a"', 1)
open(p, 'w').write(t)
print('patched gcc13 compatibility')
