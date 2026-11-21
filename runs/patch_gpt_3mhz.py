p = '/tmp/qemu-11.1.0/hw/timer/imx_gpt.c'
s = open(p).read()
old = '''    s->freq = imx_ccm_get_clock_frequency(s->ccm,
                                          s->clocks[clksrc]) / (1 + s->pr);

    trace_imx_gpt_set_freq(clksrc, s->freq);'''
new = '''    s->freq = imx_ccm_get_clock_frequency(s->ccm,
                                          s->clocks[clksrc]) / (1 + s->pr);
    /*
     * i.MX6UL Linux selects GPT CLKSRC=5 (ipg_clk_s) and expects 3MHz.
     * QEMU's CLK_IPG is 66MHz, which would make guest time 22x fast.
     */
    if (clksrc == 5) {
        s->freq = 3000000 / (1 + s->pr);
    }

    trace_imx_gpt_set_freq(clksrc, s->freq);'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w').write(s)
print('patched')
