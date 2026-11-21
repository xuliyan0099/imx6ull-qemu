import socket
import subprocess
import time
from pathlib import Path

QEMU = "./bin/qemu-system-arm-linux"
MON = "/tmp/qemu-mon.sock"
SERIAL_PORT = 4466
LOG = "/tmp/uboot-linux-boot.log"


def read_until(sock, marker, timeout=30):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        try:
            data = sock.recv(4096)
        except socket.timeout:
            continue
        if not data:
            break
        buf += data
        print(data.decode("utf-8", "replace"), end="", flush=True)
        if marker in buf:
            return buf
    return buf


def drain(sock, seconds):
    end = time.time() + seconds
    while time.time() < end:
        try:
            data = sock.recv(4096)
        except socket.timeout:
            continue
        if data:
            print(data.decode("utf-8", "replace"), end="", flush=True)


Path(LOG).write_text("")
cmd = [
    "timeout", "90", QEMU,
    "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
    "-drive", "if=sd,index=0,format=raw,file=fat:rw:/tmp/vvfat",
    "-drive", "if=sd,index=1,format=raw,file=images/uboot-emmc.img",
    "-serial", f"tcp:127.0.0.1:{SERIAL_PORT},server=on,wait=off",
    "-monitor", f"unix:{MON},server=on,wait=off",
    "-display", "none", "-no-reboot",
]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

ser = None
for _ in range(30):
    try:
        ser = socket.create_connection(("127.0.0.1", SERIAL_PORT), timeout=1)
        ser.settimeout(0.1)
        break
    except OSError:
        time.sleep(0.5)
assert ser is not None, "serial port did not open"

mon = None
for _ in range(10):
    try:
        mon = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        mon.connect(MON)
        mon.settimeout(0.1)
        break
    except OSError:
        time.sleep(0.5)

ser.sendall(b"\r")
read_until(ser, b"=>", 20)
ser.sendall(b"mmc dev 0\r")
drain(ser, 1)
for line in (
    "fatload mmc 0:1 0x80800000 zimage",
    "fatload mmc 0:1 0x83000000 board-alientek-full.dtb",
    "fatload mmc 0:1 0x84000000 ramdisk.uimg",
):
    ser.sendall((line + "\r").encode())
    read_until(ser, b"=>", 25)
ser.sendall(b"setenv bootargs console=ttymxc0,115200 root=/dev/ram0 rw\r")
drain(ser, 1)
ser.sendall(b"bootz 0x80800000 0x84000000 0x83000000\r")
read_until(ser, b"/ #", 45)

# Ask the guest for framebuffer geometry, then use QEMU's monitor to read it.
ser.sendall(b"cat /sys/class/graphics/fb0/bits_per_pixel; echo BPP; cat /sys/class/graphics/fb0/stride; echo STR; cat /sys/class/graphics/fb0/virtual_size; echo VIRT\r")
read_until(ser, b"VIRT", 10)
if mon:
    mon.sendall(b"screendump /tmp/lcd.ppm\n")
    time.sleep(2)

print("\n=== done ===")
proc.terminate()
