import re
p = '/tmp/qemu-11.1.0/hw/timer/imx_gpt.c'
text = open(p).read()
old = '''    } else {
        /*
         * Free-run GPT from reset at 3 MHz.  Linux pinctrl may call
         * udelay() before the GPT clocksource driver has programmed CR;
         * starting the counter here avoids an endless __timer_delay loop.
         */
        s->cr = GPT_CR_EN | GPT_CR_FRR | (5 << GPT_CR_CLKSRC_SHIFT);
    }
'''
new = '''    } else {
        s->cr = 0;
    }
'''
if old not in text:
    raise SystemExit('free-run block not found')
text = text.replace(old, new, 1)
open(p, 'w').write(text)
print('reverted gpt free-run')
