import io
p = '/tmp/qemu-11.1.0/hw/timer/imx_gpt.c'
s = open(p).read()
old = '''    s->freq = imx_ccm_get_clock_frequency(s->ccm,
                                          s->clocks[clksrc]) / (1 + s->pr);
'''
new = '''    s->freq = imx_ccm_get_clock_frequency(s->ccm,
                                          s->clocks[clksrc]) / (1 + s->pr);
    fprintf(stderr, "[GPT] clksrc=%u cr=%08x pr=%u freq=%lld\\n",
            clksrc, s->cr, s->pr, (long long)s->freq);
'''
if new not in s:
    s = s.replace(old, new)
open(p, 'w').write(s)
print('patched', new in s)
