import socket
import subprocess
import time
from pathlib import Path

QEMU = "./bin/qemu-system-arm-linux"
MON = "/tmp/qemu-official-mon.sock"
SERIAL = 4481
LOG = Path("runs/official-linux-boot.log")
PPM = "/tmp/lcd-official.ppm"

cmd = [
    "timeout", "140", QEMU,
    "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
    "-drive", "if=sd,index=0,format=raw,file=fat:rw:/tmp/vvfat",
    "-drive", "if=sd,index=1,format=raw,file=images/uboot-emmc.img",
    "-nic", "user,model=imx.enet", "-nic", "user,model=imx.enet",
    "-serial", f"tcp:127.0.0.1:{SERIAL},server=on,wait=off",
    "-monitor", f"unix:{MON},server=on,wait=off",
    "-display", "none", "-no-reboot",
]
Path(PPM).unlink(missing_ok=True)
Path(MON).unlink(missing_ok=True)
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

ser = None
for _ in range(30):
    try:
        ser = socket.create_connection(("127.0.0.1", SERIAL), timeout=1)
        ser.settimeout(0.1)
        break
    except OSError:
        time.sleep(0.5)
assert ser is not None, "serial port not open"

mon = None
for _ in range(10):
    try:
        mon = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        mon.connect(MON)
        mon.settimeout(0.1)
        break
    except OSError:
        time.sleep(0.5)

buf = ""


def read_until(marker, timeout=60):
    global buf
    end = time.time() + timeout
    while time.time() < end:
        try:
            data = ser.recv(4096)
        except socket.timeout:
            continue
        if data:
            text = data.decode("utf-8", "replace")
            print(text, end="", flush=True)
            buf += text
            if marker in buf:
                return True
    return False


ser.sendall(b"\r")
read_until("=>", 25)
ser.sendall(b"mmc dev 0\r")
time.sleep(0.4)
for line in (
    "fatload mmc 0:1 0x80800000 zimage-official",
    "fatload mmc 0:1 0x83000000 board-alientek-full.dtb",
    "fatload mmc 0:1 0x84000000 ramdisk.uimg",
):
    ser.sendall((line + "\r").encode())
    read_until("=>", 30)
ser.sendall(b"setenv bootargs console=ttymxc0,115200 root=/dev/ram0 rw\r")
time.sleep(0.5)
ser.sendall(b"bootz 0x80800000 0x84000000 0x83000000\r")
read_until("/ #", 75)

for line in (
    "uname -a",
    "cat /proc/version",
    "free",
    "cat /proc/partitions",
    "dmesg | grep -E 'Linux version|mxsfb|fec|mmcblk|Console:'",
    "ls /",
):
    print("\n>>>", line, flush=True)
    ser.sendall((line + "\r").encode())
    time.sleep(1)
    end = time.time() + 5
    while time.time() < end:
        try:
            data = ser.recv(4096)
            if data:
                text = data.decode("utf-8", "replace")
                print(text, end="", flush=True)
                buf += text
        except socket.timeout:
            pass

if mon:
    mon.sendall(b"screendump " + PPM.encode() + b"\n")
    time.sleep(3)

LOG.write_text(buf, encoding="utf-8")
print("\nlog:", LOG)
proc.terminate()
