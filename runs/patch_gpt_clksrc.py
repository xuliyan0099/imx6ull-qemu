p = '/tmp/qemu-11.1.0/hw/timer/imx_gpt.c'
s = open(p).read()
old = '''static const IMXClk imx6ul_gpt_clocks[] = {
    CLK_NONE,      /* 000 No clock source */
    CLK_IPG,       /* 001 ipg_clk, 532MHz*/
    CLK_IPG_HIGH,  /* 010 ipg_clk_highfreq */
    CLK_EXT,       /* 011 External clock */
    CLK_32k,       /* 100 ipg_clk_32k */
    CLK_NONE,      /* 101 not defined */
    CLK_NONE,      /* 110 not defined */
    CLK_NONE,      /* 111 not defined */
};'''
new = '''static const IMXClk imx6ul_gpt_clocks[] = {
    CLK_NONE,      /* 000 No clock source */
    CLK_IPG,       /* 001 ipg_clk */
    CLK_IPG_HIGH,  /* 010 ipg_clk_highfreq */
    CLK_EXT,       /* 011 External clock */
    CLK_32k,       /* 100 ipg_clk_32k */
    CLK_IPG,       /* 101 ipg_clk_s, used by i.MX6UL Linux */
    CLK_IPG,       /* 110 ipg_clk_s */
    CLK_IPG,       /* 111 ipg_clk_s */
};'''
assert old in s
s = s.replace(old, new)
open(p, 'w').write(s)
print('table patched')
