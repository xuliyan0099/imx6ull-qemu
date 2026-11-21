import struct, zlib
from pathlib import Path

src = Path("/tmp/vvfat/initramfs.cpio.gz").read_bytes()
name = b"ramdisk"
hdr = bytearray(64)
struct.pack_into(">I", hdr, 0, 0x27051956)
struct.pack_into(">I", hdr, 4, 0)              # hcrc, filled later
struct.pack_into(">I", hdr, 8, 0)              # time
struct.pack_into(">I", hdr, 12, len(src))      # data size
struct.pack_into(">I", hdr, 16, 0x84000000)    # load
struct.pack_into(">I", hdr, 20, 0x84000000)    # entry
struct.pack_into(">I", hdr, 24, zlib.crc32(src) & 0xffffffff)
hdr[28] = 5   # IH_OS_LINUX
hdr[29] = 2   # IH_ARCH_ARM
hdr[30] = 3   # IH_TYPE_RAMDISK
hdr[31] = 1   # IH_COMP_GZIP
hdr[32:32 + len(name)] = name
struct.pack_into(">I", hdr, 4, zlib.crc32(bytes(hdr)) & 0xffffffff)
out = Path("/tmp/vvfat/ramdisk.uimg")
out.write_bytes(bytes(hdr) + src)
print(out, len(src) + 64)
