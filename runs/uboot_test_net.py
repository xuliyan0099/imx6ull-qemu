import socket
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

PORT = 4477
HTTP_PORT = 8000


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        print("HTTP", *args, flush=True)


httpd = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), partial(Handler, directory="/tmp/vvfat"))
threading.Thread(target=httpd.serve_forever, daemon=True).start()

cmd = [
    "timeout", "95", "./bin/qemu-system-arm-linux",
    "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
    "-drive", "if=sd,index=0,format=raw,file=fat:rw:/tmp/vvfat",
    "-drive", "if=sd,index=1,format=raw,file=images/uboot-emmc.img",
    "-nic", "user,model=imx.enet", "-nic", "user,model=imx.enet",
    "-serial", f"tcp:127.0.0.1:{PORT},server=on,wait=off",
    "-display", "none", "-no-reboot",
]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
ser = None
for _ in range(30):
    try:
        ser = socket.create_connection(("127.0.0.1", PORT), timeout=1)
        ser.settimeout(0.1)
        break
    except OSError:
        time.sleep(0.5)
assert ser is not None


def read_until(marker, timeout=30):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        try:
            data = ser.recv(4096)
        except socket.timeout:
            continue
        if not data:
            continue
        buf += data
        print(data.decode("utf-8", "replace"), end="", flush=True)
        if marker in buf:
            return buf
    return buf


ser.sendall(b"\r")
read_until(b"=>", 20)
ser.sendall(b"mmc dev 0\r")
time.sleep(0.5)
for line in (
    "fatload mmc 0:1 0x80800000 zimage",
    "fatload mmc 0:1 0x83000000 board-alientek-full.dtb",
    "fatload mmc 0:1 0x84000000 ramdisk.uimg",
):
    ser.sendall((line + "\r").encode())
    read_until(b"=>", 25)
ser.sendall(b"setenv bootargs console=ttymxc0,115200 root=/dev/ram0 rw\r")
time.sleep(0.5)
ser.sendall(b"bootz 0x80800000 0x84000000 0x83000000\r")
read_until(b"/ #", 45)

for line in (
    "ifconfig eth0 10.0.2.15 netmask 255.255.255.0 up",
    "busybox --list | grep -E 'wget|nc|tftp'",
    "busybox wget -O /tmp/probe.bin http://10.0.2.2:8000/ramdisk.uimg",
    "ls -l /tmp/probe.bin",
):
    print("\n>>>", line, flush=True)
    ser.sendall((line + "\r").encode())
    time.sleep(1)
    end = time.time() + 12
    while time.time() < end:
        try:
            data = ser.recv(4096)
            if data:
                print(data.decode("utf-8", "replace"), end="", flush=True)
        except socket.timeout:
            pass

proc.terminate()
httpd.shutdown()
