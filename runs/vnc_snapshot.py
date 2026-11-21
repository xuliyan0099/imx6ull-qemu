import socket, struct, sys, zlib

host, port, output = sys.argv[1], int(sys.argv[2]), sys.argv[3]
s = socket.create_connection((host, port), 10)
s.settimeout(10)

def recv_exact(n):
    data = b''
    while len(data) < n:
        chunk = s.recv(n - len(data))
        if not chunk:
            raise RuntimeError('VNC connection closed')
        data += chunk
    return data

version = recv_exact(12)
print('server', version.decode(errors='replace').strip())
s.sendall(b'RFB 003.008\n')
count = recv_exact(1)[0]
types = recv_exact(count)
print('security types', list(types))
if 1 not in types:
    raise RuntimeError('VNC server does not offer None security')
s.sendall(struct.pack('!B', 1))
result = struct.unpack('!I', recv_exact(4))[0]
if result != 0:
    raise RuntimeError(f'VNC security failed: {result}')
s.sendall(struct.pack('!B', 1))
width, height, pixel = struct.unpack('!HH', recv_exact(4)) + (recv_exact(16),)
name_len = struct.unpack('!I', recv_exact(4))[0]
name = recv_exact(name_len).decode(errors='replace')
print('desktop', width, height, name)
print('pixel format', pixel)

s.sendall(struct.pack('!B3x', 0) + struct.pack('!BBBBHHHBBB3x', 32, 24, 0, 1, 255, 255, 255, 16, 8, 0))
s.sendall(struct.pack('!BxH', 2, 1) + struct.pack('!I', 0))
s.sendall(struct.pack('!BBHHHH', 3, 0, 0, 0, width, height))

while True:
    msg_type = recv_exact(1)[0]
    if msg_type == 0:
        recv_exact(1)
        nrects = struct.unpack('!H', recv_exact(2))[0]
        for _ in range(nrects):
            x, y, w, h, enc = struct.unpack('!HHHHI', recv_exact(12))
            if enc != 0:
                raise RuntimeError(f'unsupported VNC encoding {enc}')
            print('rect', x, y, w, h, 'raw')
            if x == 0 and y == 0 and w == width and h == height:
                data = recv_exact(w * h * 4)
                break
            recv_exact(w * h * 4)
        else:
            continue
        break
    if msg_type == 1:
        recv_exact(3)
        continue
    if msg_type == 2:
        continue
    if msg_type == 3:
        recv_exact(7)
        continue
    raise RuntimeError(f'unknown VNC message {msg_type}')

rows = []
for row in range(height):
    line = bytearray()
    base = row * width * 4
    for col in range(width):
        b, g, r, _ = data[base + col * 4:base + col * 4 + 4]
        line += bytes((r, g, b))
    rows.append(bytes(line))

row_size = (width * 3 + 3) & ~3
pixels = bytearray()
for line in reversed(rows):
    pixels += line + b'\x00' * (row_size - width * 3)
bmp = bytearray()
bmp += b'BM' + struct.pack('<IHHI', 54 + len(pixels), 0, 0, 54)
bmp += struct.pack('<IiiHHIIiiII', 40, width, height, 1, 24, 0, len(pixels), 2835, 2835, 0, 0)
bmp += pixels
open(output, 'wb').write(bmp)
print('wrote', output, len(bmp))
