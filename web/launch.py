"""Restart this project's default web service and its QEMU session."""
import fcntl
import hashlib
import os
import signal
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
VNC = '127.0.0.1:77'
QEMU_FILES = {
    str(ROOT / 'bin' / name)
    for name in ('qemu-system-arm-linux', 'qemu-system-arm-graphics-linux',
                 'qemu-system-arm-official-linux')
}


def matching_processes():
    services = set()
    emulators = set()
    for path in Path('/proc').iterdir():
        if not path.name.isdigit() or int(path.name) == os.getpid():
            continue
        try:
            args = [os.fsdecode(arg) for arg in
                    (path / 'cmdline').read_bytes().split(b'\0') if arg]
            if not args:
                continue
            cwd = (path / 'cwd').resolve()
            executable = Path(args[0])
            if not executable.is_absolute():
                executable = cwd / executable
            if str(executable) in QEMU_FILES and '-vnc' in args:
                index = args.index('-vnc') + 1
                if index < len(args) and args[index] == VNC:
                    emulators.add(int(path.name))
            if len(args) >= 2 and Path(args[0]).name.startswith('python'):
                script = Path(args[1])
                if not script.is_absolute():
                    script = cwd / script
                if script.resolve() == ROOT / 'web/server.py':
                    environment = dict(entry.split(b'=', 1) for entry in
                                       (path / 'environ').read_bytes().split(b'\0')
                                       if b'=' in entry)
                    if environment.get(b'IM6_WEB_PORT', b'8765') == b'8765':
                        services.add(int(path.name))
        except (OSError, ValueError):
            continue
    return services, emulators


def terminate_previous():
    services, emulators = matching_processes()
    if services or emulators:
        print('正在结束上一次虚拟开发板会话，临时磁盘写入将丢弃。', flush=True)
    for pid in services:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        live_services, live_emulators = matching_processes()
        if not (services & live_services or emulators & live_emulators):
            break
        time.sleep(.1)
    # Recheck ownership before signalling any processes left after cleanup.
    live_services, live_emulators = matching_processes()
    for pid in services & live_services:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    for pid in emulators & live_emulators:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        live_services, live_emulators = matching_processes()
        if not (services & live_services or emulators & live_emulators):
            return
        time.sleep(.1)
    for pid in emulators & live_emulators:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(.1)


def main():
    identity = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:16]
    with open('/tmp/im6-launch-' + identity + '.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        terminate_previous()
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(('127.0.0.1', PORT))
            except OSError as exc:
                raise RuntimeError('端口 8765 仍被占用，请检查占用程序。') from exc
        os.chdir(ROOT)
        environment = os.environ.copy()
        environment['PYTHONPATH'] = str(ROOT / 'web/deps')
        environment['IM6_WEB_PORT'] = str(PORT)
        environment['IM6_VNC_DISPLAY'] = '77'
        print('正在启动新的虚拟开发板服务。', flush=True)
        os.execvpe('python3', ['python3', 'web/server.py'], environment)


if __name__ == '__main__':
    main()
