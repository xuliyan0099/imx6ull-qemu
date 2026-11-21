import struct
W, H = 800, 480
bars = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (255, 255, 255), (0, 0, 0),
]
out = bytearray()
for y in range(H):
    for x in range(W):
        r, g, b = bars[min(x * len(bars) // W, len(bars) - 1)]
        v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        out += struct.pack('<H', v)
open(r'D:\Workspace\StudyNote\IM6\qemu\runs\linux-fb-bars565.raw', 'wb').write(out)
print(len(out))
