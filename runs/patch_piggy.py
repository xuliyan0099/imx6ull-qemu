import glob
for p in glob.glob('/tmp/linux-imx/arch/arm/boot/compressed/piggy.*.S'):
    t = open(p).read()
    t = t.replace('.section .piggydata,#alloc', '.section .piggydata,"a"')
    open(p, 'w').write(t)
    print('patched', p)
