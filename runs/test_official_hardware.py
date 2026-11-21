"""Cold boot and Goodix click regression. Uses an isolated board and temporary overlays."""
import asyncio
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault('IM6_VNC_DISPLAY', '92')
sys.path.insert(0, str(ROOT / 'web'))
import server

async def main():
    board = server.Board()
    transmitted = bytearray()
    connect_unix = board.connect_unix

    class SerialRecorder:
        def __init__(self, writer):
            self.writer = writer

        def write(self, data):
            transmitted.extend(data)
            self.writer.write(data)

        def __getattr__(self, name):
            return getattr(self.writer, name)

    async def recorded_connection(name):
        reader, writer = await connect_unix(name)
        return reader, SerialRecorder(writer) if name == 'serial' else writer

    board.connect_unix = recorded_connection
    try:
        await board.start('linux-official')
        print(str(board.work), flush=True)
        for elapsed in range(240):
            await asyncio.sleep(1)
            if elapsed % 20 == 0:
                print(elapsed, board.boot_state, board.boot_message, flush=True)
                (ROOT / 'runs/official-hardware-boot.log').write_bytes(board.history)
                await board.command('screendump', {'filename': str(ROOT / 'runs/official-hardware.ppm')})
            if b'Internal error: Oops' in board.history:
                raise RuntimeError('Kernel Oops during cold boot')
            if board.boot_state == 'manual':
                raise RuntimeError(board.boot_message)
            if elapsed >= 120 and board.boot_state == 'ready':
                break
        (ROOT / 'runs/official-hardware-boot.log').write_bytes(board.history)
        await board.command('screendump', {'filename': str(ROOT / 'runs/official-hardware.ppm')})
        assert board.boot_state == 'ready', board.boot_message
        expected = (b'setenv bootargs console=ttymxc0,115200 root=/dev/mmcblk0 rootwait rw\r'
                    b'bootz 0x80800000 - 0x83000000\r')
        assert bytes(transmitted).replace(b'\x1b[30;100R', b'') == expected
        assert b'GTP works in interrupt mode.' in board.history
        print('PASS cold boot, native Goodix probe, zero Linux shell commands', flush=True)
        await board.command('input-send-event', {'events': [
            {'type': 'abs', 'data': {'axis': 'x', 'value': 708 * 32767 // 799}},
            {'type': 'abs', 'data': {'axis': 'y', 'value': 100 * 32767 // 479}},
            {'type': 'btn', 'data': {'button': 'left', 'down': True}},
        ]})
        await asyncio.sleep(.3)
        await board.command('input-send-event', {'events': [
            {'type': 'btn', 'data': {'button': 'left', 'down': False}},
        ]})
        await asyncio.sleep(35)
        await board.command('screendump', {'filename': str(ROOT / 'runs/official-hardware-touch.ppm')})
        print('Captured desktop and settings click for visual verification', flush=True)
    finally:
        if board.history:
            (ROOT / 'runs/official-hardware-boot.log').write_bytes(board.history)
        (ROOT / 'runs/official-hardware-serial-tx.bin').write_bytes(transmitted)
        await board.stop()

asyncio.run(main())
