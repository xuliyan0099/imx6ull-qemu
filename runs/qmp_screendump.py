import json
import socket
import sys

path = sys.argv[1]
out = sys.argv[2]

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(path)

def recv_json():
    buf = b""
    while not buf.endswith(b"\n"):
        buf += s.recv(4096)
    return json.loads(buf.decode())

print("greeting:", recv_json())
s.sendall(b'{"execute":"qmp_capabilities"}\n')
print("cap:", recv_json())
s.sendall((json.dumps({"execute": "screendump", "arguments": {"filename": out}}) + "\n").encode())
print("screendump:", recv_json())
s.close()
