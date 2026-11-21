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
        out += struct.pack('<I', (r << 16) | (g << 8) | b)
open(r'D:\Workspace\StudyNote\IM6\qemu\runs\linux-fb-bars.raw', 'wb').write(out)
print(len(out))
