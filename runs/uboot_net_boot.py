import os
import socket
import subprocess
import sys
import time

QDIR = "/mnt/d/Workspace/StudyNote/IM6/qemu"
PORT = 4444
cmd = [
    "timeout", "60", "./bin/qemu-system-arm-linux",
    "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
    "-drive", "if=sd,index=0,format=raw,file=images/tf.img",
    "-drive", "if=sd,index=1,format=raw,file=images/uboot-emmc.img",
    "-nic", "user,model=imx.enet,tftp=" + QDIR + "/images",
    "-nic", "user,model=imx.enet",
    "-serial", "tcp:127.0.0.1:%d,server=on,wait=off" % PORT,
    "-display", "none", "-no-reboot",
]
proc = subprocess.Popen(cmd, cwd=QDIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
buf = b""

def connect():
    for _ in range(20):
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=1)
            s.settimeout(0.2)
            return s
        except OSError:
            time.sleep(0.5)
    raise SystemExit("serial socket not ready")

sock = connect()

def read_for(seconds):
    global buf
    end = time.time() + seconds
    while time.time() < end:
        try:
            d = sock.recv(4096)
            if d:
                buf += d
                print(d.decode("utf-8", "replace"), end="", flush=True)
        except socket.timeout:
            pass
        if b"=> " in buf:
            return True
    return False

def send(text):
    print("\n[SEND] %r" % text)
    sock.sendall(text.encode() + b"\r")
    time.sleep(0.8)

read_for(6)
send("")  # stop autoboot
read_for(4)
for line in [
    "setenv ethaddr 00:04:9f:04:d2:35",
    "setenv ipaddr 10.0.2.15",
    "setenv serverip 10.0.2.2",
    "setenv netmask 255.255.255.0",
    "setenv bootargs console=ttymxc0,115200 rdinit=/init ignore_loglevel",
    "tftp 0x80800000 zImage-nxp-fb",
    "tftp 0x83000000 board-alientek-full.dtb",
    "tftp 0x84000000 initramfs.cpio.gz",
    "bootz 0x80800000 0x84000000 0x83000000",
]:
    send(line)
    read_for(4)
read_for(15)
try:
    proc.terminate()
except Exception:
    pass
print("\n\n[exit]", proc.wait(timeout=5))
