import struct
import zlib
from pathlib import Path

src = Path("/tmp/lcd.ppm").read_bytes()
# P6\n800 480\n255\n
header_end = src.find(b"\n", src.find(b"\n", src.find(b"\n") + 1) + 1) + 1
idx = 0
lines = []
while len(lines) < 3:
    end = src.find(b"\n", idx)
    lines.append(src[idx:end])
    idx = end + 1
magic, dims, maxval = lines[0], lines[1], lines[2]
width, height = map(int, dims.split())
pixels = src[idx:idx + width * height * 3]
print(magic, width, height, maxval, len(pixels))

raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))


def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))


png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 6))
       + chunk(b"IEND", b""))
out = Path("/mnt/d/Workspace/StudyNote/IM6/qemu/runs/uboot-linux-lcd.png")
out.write_bytes(png)
print(out, out.stat().st_size)
