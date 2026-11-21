import socket, time, sys

path = "/tmp/mon"
s = socket.socket(socket.AF_UNIX)
s.connect(path)
for cmd in sys.argv[1:]:
    s.sendall((cmd + "\n").encode())
    time.sleep(0.8)
    print(s.recv(65536).decode(errors="replace"))
s.sendall(b"quit\n")
