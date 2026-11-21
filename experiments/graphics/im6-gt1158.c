/* Experimental GT1158 subset for the existing i.MX6ULL FreeRTOS driver. */
#include "qemu/osdep.h"
#include "hw/i2c/i2c.h"
#include "ui/input.h"
#include "qemu/module.h"
#define TYPE_IM6_GT "im6-gt1158"
OBJECT_DECLARE_SIMPLE_TYPE(IM6GTState, IM6_GT)
struct IM6GTState {
    I2CSlave parent_obj;
    uint16_t reg;
    uint8_t index;
    int x, y;
    bool down, delivered_down;
    struct { int x, y; bool down; } frames[32];
    unsigned head, count;
    QemuInputHandlerState *handler;
};
static int gt_event(I2CSlave *dev, enum i2c_event event)
{
    IM6GTState *s = IM6_GT(dev);
    if (event == I2C_START_SEND) s->index = 0;
    return 0;
}
static int gt_send(I2CSlave *dev, uint8_t value)
{
    IM6GTState *s = IM6_GT(dev);
    if (s->index == 0) s->reg = (uint16_t)value << 8;
    else if (s->index == 1) s->reg |= value;
    else { if (s->reg == 0x814e && value == 0 && s->count) { s->head = (s->head + 1) % 32; s->count--; } s->reg++; }
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
    case 0x8140: return '1'; case 0x8141: return '1';
    case 0x8142: return '5'; case 0x8143: return '8';
    case 0x8051: return 0x20; case 0x8052: return 0x03;
    case 0x8053: return 0xe0; case 0x8054: return 0x01;
    case 0x814e: return s->count ? (0x80 | (down ? 1 : 0)) : 0;
    case 0x8150: return x & 0xff; case 0x8151: return (x >> 8) & 0xff;
    case 0x8152: return y & 0xff; case 0x8153: return (y >> 8) & 0xff;
    default: return 0;
    }
}
static void gt_input(DeviceState *dev, QemuConsole *src, QemuInputEvent *evt)
{
    IM6GTState *s = IM6_GT(dev);
    if (evt->type == INPUT_EVENT_KIND_ABS) {
        if (evt->abs.axis == INPUT_AXIS_X) s->x = MIN(799, MAX(0, evt->abs.value * 799 / 0x7fff));
        if (evt->abs.axis == INPUT_AXIS_Y) s->y = MIN(479, MAX(0, evt->abs.value * 479 / 0x7fff));
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
        if (s->frames[last].x == s->x && s->frames[last].y == s->y && s->frames[last].down == s->down) return;
    } else if (!s->down && !s->delivered_down) {
        return;
    }
    if (s->count == 32) s->count--; /* Preserve the latest release if overloaded. */
    tail = (s->head + s->count) % 32;
    s->frames[tail].x = s->x; s->frames[tail].y = s->y; s->frames[tail].down = s->down;
    s->count++; s->delivered_down = s->down;
}
static const QemuInputHandler gt_handler = {
    .name = "GT1158 touchscreen", .mask = INPUT_EVENT_MASK_BTN | INPUT_EVENT_MASK_ABS,
    .event = gt_input, .sync = gt_sync,
};
static void gt_realize(DeviceState *dev, Error **errp)
{
    IM6GTState *s = IM6_GT(dev);
    s->handler = qemu_input_handler_register(dev, &gt_handler);
    qemu_input_handler_activate(s->handler);
}
static void gt_class_init(ObjectClass *klass, const void *data)
{
    DeviceClass *dc = DEVICE_CLASS(klass);
    I2CSlaveClass *ic = I2C_SLAVE_CLASS(klass);
    dc->realize = gt_realize; ic->event = gt_event; ic->send = gt_send; ic->recv = gt_recv;
}
static const TypeInfo gt_info = { .name=TYPE_IM6_GT, .parent=TYPE_I2C_SLAVE,
    .instance_size=sizeof(IM6GTState), .class_init=gt_class_init };
static void gt_register(void) { type_register_static(&gt_info); }
type_init(gt_register)

