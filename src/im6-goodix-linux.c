/* Single-contact Goodix model for the vendor Linux gt9xx driver. */
#include "qemu/osdep.h"
#include "hw/i2c/i2c.h"
#include "ui/input.h"
#include "qemu/module.h"
#include "hw/core/irq.h"
#include "hw/core/qdev.h"
#include "qemu/timer.h"
#define TYPE_IM6_GT "im6-goodix-linux"
OBJECT_DECLARE_SIMPLE_TYPE(IM6GTState, IM6_GT)
struct IM6GTState {
    I2CSlave parent_obj;
    uint16_t reg;
    unsigned index;
    qemu_irq irq;
    QEMUTimer *irq_timer;
    int x;
    int y;
    bool down;
    bool delivered_down;
    struct {
        int x;
        int y;
        bool down;
    } frames[32];
    unsigned head;
    unsigned count;
    QemuInputHandlerState *handler;
};
static void gt_irq(void *opaque)
{
    IM6GTState *s = opaque;
    qemu_set_irq(s->irq, s->count ? 0 : 1);
}

static int gt_event(I2CSlave *dev, enum i2c_event event)
{
    IM6GTState *s = IM6_GT(dev);
    if (event == I2C_START_SEND) {
        s->index = 0;
    }
    return 0;
}
static int gt_send(I2CSlave *dev, uint8_t value)
{
    IM6GTState *s = IM6_GT(dev);
    if (s->index == 0) {
        s->reg = (uint16_t)value << 8;
    } else if (s->index == 1) {
        s->reg |= value;
    } else {
        if (s->reg == 0x814e && value == 0 && s->count) {
            s->head = (s->head + 1) % G_N_ELEMENTS(s->frames);
            s->count--;
            qemu_set_irq(s->irq, 1);
            /* Deliver the next edge after the guest unmasks its IRQ. */
            if (s->count) {
                timer_mod(s->irq_timer,
                          qemu_clock_get_ms(QEMU_CLOCK_VIRTUAL) + 10);
            }
        }
        s->reg++;
    }
    s->index++;
    return 0;
}
static uint8_t gt_recv(I2CSlave *dev)
{
    IM6GTState *s = IM6_GT(dev);
    uint16_t r = s->reg++;
    int x = s->count ? s->frames[s->head].x : s->x;
    int y = s->count ? s->frames[s->head].y : s->y;
    bool down = s->count && s->frames[s->head].down;
    switch (r) {
    case 0x8140: return '1';
    case 0x8141: return '1';
    case 0x8142: return '5';
    case 0x8143: return '8';
    case 0x8048: return 0x20;
    case 0x8049: return 0x03;
    case 0x804a: return 0xe0;
    case 0x804b: return 0x01;
    case 0x804d: case 0x8056: return 1; /* Falling-edge IRQ. */
    case 0x8051: return 0x20;
    case 0x8052: return 0x03;
    case 0x8053: return 0xe0;
    case 0x8054: return 0x01;
    case 0x814e: return s->count ? (0x80 | (down ? 1 : 0)) : 0;
    case 0x8150: return x & 0xff;
    case 0x8151: return (x >> 8) & 0xff;
    case 0x8152: return y & 0xff;
    case 0x8153: return (y >> 8) & 0xff;
    case 0x8154: return down ? 1 : 0;
    default: return 0;
    }
}
static void gt_input(DeviceState *dev, QemuConsole *src, QemuInputEvent *evt)
{
    IM6GTState *s = IM6_GT(dev);
    if (evt->type == INPUT_EVENT_KIND_ABS) {
        if (evt->abs.axis == INPUT_AXIS_X) {
            s->x = MIN(799, MAX(0, evt->abs.value * 799 / 0x7fff));
        }
        if (evt->abs.axis == INPUT_AXIS_Y) {
            s->y = MIN(479, MAX(0, evt->abs.value * 479 / 0x7fff));
        }
    } else if (evt->type == INPUT_EVENT_KIND_BTN && evt->btn.button == INPUT_BUTTON_LEFT) {
        s->down = evt->btn.down;
    }
}
static void gt_sync(DeviceState *dev)
{
    IM6GTState *s = IM6_GT(dev);
    unsigned tail;
    if (s->count) {
        unsigned last = (s->head + s->count - 1) % 32;
        if (s->frames[last].x == s->x && s->frames[last].y == s->y &&
            s->frames[last].down == s->down) {
            return;
        }
    } else if (!s->down && !s->delivered_down) {
        return;
    }
    if (s->count == G_N_ELEMENTS(s->frames)) {
        /* Keep the frame being read stable and replace the newest frame. */
        s->count--;
    }
    tail = (s->head + s->count) % 32;
    s->frames[tail].x = s->x;
    s->frames[tail].y = s->y;
    s->frames[tail].down = s->down;
    s->count++;
    s->delivered_down = s->down;
    if (s->count == 1) {
        /* The guest drives INT low during address selection and reset. */
        qemu_set_irq(s->irq, 1);
        timer_mod(s->irq_timer, qemu_clock_get_ms(QEMU_CLOCK_VIRTUAL) + 1);
    }
}
static const QemuInputHandler gt_handler = {
    .name = "Goodix Linux touchscreen", .mask = INPUT_EVENT_MASK_BTN | INPUT_EVENT_MASK_ABS,
    .event = gt_input, .sync = gt_sync,
};
static void gt_realize(DeviceState *dev, Error **errp)
{
    IM6GTState *s = IM6_GT(dev);
    qdev_init_gpio_out(dev, &s->irq, 1);
    s->irq_timer = timer_new_ms(QEMU_CLOCK_VIRTUAL, gt_irq, s);
    qemu_set_irq(s->irq, 1);
    s->handler = qemu_input_handler_register(dev, &gt_handler);
    qemu_input_handler_activate(s->handler);
}
static void gt_reset(DeviceState *dev)
{
    IM6GTState *s = IM6_GT(dev);
    timer_del(s->irq_timer);
    s->reg = s->index = s->head = s->count = 0;
    s->down = s->delivered_down = false;
    s->x = s->y = 0;
    qemu_set_irq(s->irq, 1);
}

static void gt_class_init(ObjectClass *klass, const void *data)
{
    DeviceClass *dc = DEVICE_CLASS(klass);
    I2CSlaveClass *ic = I2C_SLAVE_CLASS(klass);
    device_class_set_legacy_reset(dc, gt_reset);
    dc->realize = gt_realize;
    ic->event = gt_event;
    ic->send = gt_send;
    ic->recv = gt_recv;
}
static const TypeInfo gt_info = {
    .name = TYPE_IM6_GT,
    .parent = TYPE_I2C_SLAVE,
    .instance_size = sizeof(IM6GTState),
    .class_init = gt_class_init,
};
static void gt_register(void)
{
    type_register_static(&gt_info);
}
type_init(gt_register)

