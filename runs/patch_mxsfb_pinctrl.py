p = '/tmp/linux-imx/drivers/video/fbdev/mxsfb.c'
t = open(p).read()
old = """\tif (!host->dispdrv) {
\t\tpinctrl = devm_pinctrl_get_select_default(&pdev->dev);
\t\tif (IS_ERR(pinctrl)) {
\t\t\tret = PTR_ERR(pinctrl);
\t\t\tgoto fb_pm_runtime_disable;
\t\t}
\t}
"""
new = """\tif (!host->dispdrv) {
\t\tpinctrl = devm_pinctrl_get_select_default(&pdev->dev);
\t\tif (IS_ERR(pinctrl)) {
\t\t\tif (PTR_ERR(pinctrl) == -EPROBE_DEFER) {
\t\t\t\tret = -EPROBE_DEFER;
\t\t\t\tgoto fb_pm_runtime_disable;
\t\t\t}
\t\t\tdev_info(&pdev->dev, "pinctrl default state unavailable, continue\\n");
\t\t\tpinctrl = NULL;
\t\t}
\t}
"""
assert old in t
open(p, 'w').write(t.replace(old, new))
print('patched mxsfb optional pinctrl')
