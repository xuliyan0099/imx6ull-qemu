import struct, zlib

def read_ppm(path):
    with open(path, 'rb') as f:
        data = f.read()
    # parse P6 header, tolerate comments
    fields = []
    i = 0
    while len(fields) < 3:
        while i < len(data) and data[i:i+1].isspace():
            i += 1
        if data[i:i+1] == b'#':
            while i < len(data) and data[i:i+1] != b'\n':
                i += 1
            continue
        start = i
        while i < len(data) and not data[i:i+1].isspace():
            i += 1
        fields.append(data[start:i])
    magic, width, height = fields[0], int(fields[1]), int(fields[2])
    i += 1  # single whitespace after maxval
    maxval = int(data[i-1:i]) if False else None
    # re-parse maxval properly: fields only 3, need one more
    # find maxval token
    tokens = []
    # rebuild from scratch robustly
    pos = 0
    def token():
        nonlocal pos
        while pos < len(data) and data[pos:pos+1].isspace():
            pos += 1
        if data[pos:pos+1] == b'#':
            while pos < len(data) and data[pos:pos+1] != b'\n':
                pos += 1
            return token()
        s = pos
        while pos < len(data) and not data[pos:pos+1].isspace():
            pos += 1
        return data[s:pos]
    magic = token(); w = int(token()); h = int(token()); maxv = int(token())
    while pos < len(data) and data[pos:pos+1].isspace():
        pos += 1
        break
    pix = data[pos:pos + w*h*3]
    return w, h, maxv, pix

def write_png(path, w, h, maxv, pix):
    # convert to 8-bit RGB
    if maxv != 255:
        pix = bytes((c * 255 + maxv//2) // maxv for c in pix)
    raw = bytearray()
    stride = w*3
    for y in range(h):
        raw.append(0)
        raw += pix[y*stride:(y+1)*stride]
    def chunk(tag, payload):
        return struct.pack('>I', len(payload)) + tag + payload + struct.pack('>I', zlib.crc32(tag + payload) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 6))
    png += chunk(b'IEND', b'')
    open(path, 'wb').write(png)

w, h, maxv, pix = read_ppm(r'D:\Workspace\StudyNote\IM6\qemu\runs\linux-fb.ppm')
write_png(r'D:\Workspace\StudyNote\IM6\qemu\runs\linux-fb.png', w, h, maxv, pix)
print(w, h, maxv, len(pix))
