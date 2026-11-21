p = '/tmp/qemu-11.1.0/hw/timer/imx_gpt.c'
s = open(p).read()
dbg = '''    fprintf(stderr, "[GPT] clksrc=%u cr=%08x pr=%u freq=%lld\\n",
            clksrc, s->cr, s->pr, (long long)s->freq);
'''
s = s.replace(dbg, '')
open(p, 'w').write(s)
print('debug removed:', dbg not in s)
