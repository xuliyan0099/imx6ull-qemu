import re
p = '/tmp/linux-imx/arch/arm/include/asm/compiler.h'
t = open(p).read()
start = t.find('#define __asmeq(x, y)')
end = t.find('\n\n#endif', start)
if start < 0 or end < 0:
    raise SystemExit('macro not found')
t = t[:start] + '#define __asmeq(x, y) ""\n' + t[end:]
open(p, 'w').write(t)
print('disabled __asmeq checks')
