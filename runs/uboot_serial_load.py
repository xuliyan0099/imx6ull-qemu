import socket
import subprocess
import sys
import time

QDIR = "/mnt/d/Workspace/StudyNote/IM6/qemu"
PORT = 4447

SOH, STX, EOT, ACK, NAK, CAN, CRC_C = 0x01, 0x02, 0x04, 0x06, 0x15, 0x18, 0x43


def crc16(data):
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xffff if crc & 0x8000 else (crc << 1) & 0xffff
    return crc


class Link:
    def __init__(self, sock):
        self.s = sock
        self.buf = b""

    def read(self, timeout=2.0):
        self.s.settimeout(0.05)
        end = time.time() + timeout
        while time.time() < end:
            try:
                d = self.s.recv(4096)
                if d:
                    self.buf += d
                    return d
            except socket.timeout:
                pass
        return b""

    def wait_byte(self, want, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            while self.buf:
                b = self.buf[0]
                self.buf = self.buf[1:]
                if b == want:
                    return True
                # discard other control bytes, but keep printable log
                if b not in (ACK, NAK, CAN, CRC_C, SOH, STX, EOT):
                    sys.stdout.write(chr(b) if 32 <= b < 127 else ".")
                    sys.stdout.flush()
            self.read(0.2)
        return False

    def send_block(self, seq, payload, size=1024):
        head = STX if size == 1024 else SOH
        payload = payload + b"\0" * (size - len(payload))
        frame = bytes([head, seq & 0xff]) + payload
        frame += bytes([(crc16(payload) >> 8) & 0xff, crc16(payload) & 0xff])
        for _ in range(5):
            self.s.sendall(frame)
            if self.wait_byte(ACK, 3):
                return True
            if self.buf and self.buf[0] == NAK:
                self.buf = self.buf[1:]
            print("retry block", seq)
        return False

    def send_file(self, filename, data):
        # block 0: name, size, padding
        hdr = (filename.encode() + b"\0" + str(len(data)).encode() + b"\0")
        if not self.send_block(0, hdr, 128):
            raise RuntimeError("block0 not acked")
        seq = 1
        for off in range(0, len(data), 1024):
            chunk = data[off:off + 1024]
            if not self.send_block(seq, chunk, 1024):
                raise RuntimeError("data block %d not acked" % seq)
            seq = (seq + 1) & 0xff
            if seq == 0:
                seq = 1
            if (off // 1024) % 100 == 0:
                print("sent %d/%d" % (off, len(data)))
        self.s.sendall(bytes([EOT]))
        if not self.wait_byte(ACK, 5):
            raise RuntimeError("EOT not acked")
        # U-Boot asks for final empty header with 'C'
        self.wait_byte(CRC_C, 5)
        if not self.send_block(0, b"", 128):
            raise RuntimeError("final header not acked")
        return True


def main():
    cmd = [
        "timeout", "120", "./bin/qemu-system-arm-linux",
        "-M", "mcimx6ull-alientek", "-m", "512", "-smp", "1",
        "-drive", "if=sd,index=0,format=raw,file=images/tf.img",
        "-drive", "if=sd,index=1,format=raw,file=images/uboot-emmc.img",
        "-serial", "tcp:127.0.0.1:%d,server=on,wait=off" % PORT,
        "-display", "none", "-no-reboot",
    ]
    p = subprocess.Popen(cmd, cwd=QDIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    sock = None
    for _ in range(20):
        try:
            sock = socket.create_connection(("127.0.0.1", PORT), timeout=1)
            break
        except OSError:
            time.sleep(0.5)
    if sock is None:
        raise SystemExit("no serial")
    link = Link(sock)
    link.read(6)
    sock.sendall(b"\r")
    time.sleep(0.5)
    sock.sendall(b"loady 0x83000000\r")
    if not link.wait_byte(CRC_C, 20):
        print("no initial C")
        p.terminate()
        return 1
    path = QDIR + "/images/board-alientek-full.dtb"
    data = open(path, "rb").read()
    link.send_file("board-alientek-full.dtb", data)
    print("\nYMODEM done")
    time.sleep(1)
    sock.sendall(b"bootz 0x80800000 0x84000000 0x83000000\r")
    link.read(10)
    p.terminate()
    print("qemu rc", p.wait())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
