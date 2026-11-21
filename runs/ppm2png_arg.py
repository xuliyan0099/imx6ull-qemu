import struct, sys, zlib

def read_ppm(path):
    data = open(path, 'rb').read()
    pos = 0
    tokens = []
    while len(tokens) < 4:
        while pos < len(data) and data[pos:pos+1].isspace():
            pos += 1
        if data[pos:pos+1] == b'#':
            while pos < len(data) and data[pos:pos+1] != b'\n':
                pos += 1
            continue
        start = pos
        while pos < len(data) and not data[pos:pos+1].isspace():
            pos += 1
        tokens.append(data[start:pos])
    magic, w, h, maxv = tokens[0], int(tokens[1]), int(tokens[2]), int(tokens[3])
    pos += 1
    pix = data[pos:pos + w * h * 3]
    return w, h, maxv, pix

def write_png(path, w, h, maxv, pix):
    if maxv != 255:
        pix = bytes((c * 255 + maxv // 2) // maxv for c in pix)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += pix[y * stride:(y + 1) * stride]
    def chunk(tag, payload):
        return struct.pack('>I', len(payload)) + tag + payload + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 6))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)

src, dst = sys.argv[1], sys.argv[2]
w, h, maxv, pix = read_ppm(src)
write_png(dst, w, h, maxv, pix)
print(w, h, maxv, len(pix))
