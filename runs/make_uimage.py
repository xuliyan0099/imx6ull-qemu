import struct, zlib, os
raw = '/tmp/vmlinux.bin'
out = '/tmp/vmlinux.uimg'
data = open(raw, 'rb').read()
# legacy uImage header
magic = 0x27051956
hdr = struct.pack('>IIIIIBBBB32s',
                  magic, 0, len(data), 0x80008000, 0x80008000,
                  5, 2, 2, 0, b'imx6ull-vmlinux')
# header CRC over 64 bytes with hcrc=0
hdr_crc = zlib.crc32(hdr) & 0xffffffff
hdr = struct.pack('>IIIIIBBBB32s',
                  magic, hdr_crc, len(data), 0x80008000, 0x80008000,
                  5, 2, 2, 0, b'imx6ull-vmlinux')
data_crc = zlib.crc32(data) & 0xffffffff
# patch dcrc field (offset 24)
hdr = hdr[:24] + struct.pack('>I', data_crc) + hdr[28:]
open(out, 'wb').write(hdr + data)
print(os.path.getsize(out), hex(hdr_crc), hex(data_crc))
