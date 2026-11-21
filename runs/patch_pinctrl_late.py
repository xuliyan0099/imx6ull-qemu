import re
p = '/tmp/linux-imx/drivers/pinctrl/freescale/pinctrl-imx6ul.c'
text = open(p).read()
if 'arch_initcall(imx6ul_pinctrl_init);' not in text:
    raise SystemExit('arch_initcall not found')
text = text.replace('arch_initcall(imx6ul_pinctrl_init);',
                    'late_initcall(imx6ul_pinctrl_init);', 1)
open(p, 'w').write(text)
print('patched pinctrl to late_initcall')
