import socket
import subprocess
import time

PORT = 4480
LOG = "runs/freertos-emmc-boot.log"

cmd = [
    "timeout", "45", "./bin/qemu-system-arm-linux",
    "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
    "-watchdog-action", "none",
    "-drive", "if=sd,index=0,format=raw,file=images/tf.img",
    "-drive", "if=sd,index=1,format=raw,file=images/emmc-uboot-freertos.img",
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

buffer = []


def drain(seconds, marker=None):
    end = time.time() + seconds
    while time.time() < end:
        try:
            data = ser.recv(4096)
        except socket.timeout:
            continue
        if data:
            text = data.decode("utf-8", "replace")
            print(text, end="", flush=True)
            buffer.append(text)
            if marker and marker in "".join(buffer):
                return True
    return False


drain(6, "=>")
for line in ("mmc dev 1", "mmc read 0x900000 0x800 0x20", "go 0x900020"):
    ser.sendall((line + "\r").encode())
    time.sleep(0.5)
    drain(5)

with open(LOG, "w", encoding="utf-8") as f:
    f.write("".join(buffer))
print(f"\nlog: {LOG}")
proc.terminate()
