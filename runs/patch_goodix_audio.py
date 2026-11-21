from pathlib import Path
p = Path('/tmp/im6-official-audio/hw/arm/mcimx6ull-alientek.c')
s = p.read_text()
old = '    qdev_realize(DEVICE(s), NULL, &error_fatal);\n'
new = '''    qdev_realize(DEVICE(s), NULL, &error_fatal);
    I2CSlave *touch = i2c_slave_create_simple(s->i2c[1].bus,
                                               "im6-goodix-linux", 0x5d);
    qdev_connect_gpio_out(DEVICE(touch), 0,
                          qdev_get_gpio_in(DEVICE(&s->gpio[0]), 9));
'''
if s.count(old) != 1:
    raise SystemExit('unexpected source')
p.write_text(s.replace(old, new))
print('patched')
