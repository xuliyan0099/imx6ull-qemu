import asyncio, os
import aiohttp

BASE = os.environ.get("IM6_TEST_BASE", "http://127.0.0.1:8765")
CMDS = [
    "cat /etc/resolv.conf",
    "busybox wget -T 10 -O /tmp/netprobe http://example.com/ 2>&1 | tail -5; ls -l /tmp/netprobe 2>/dev/null",
    "ping -c 2 223.5.5.5 2>&1 | tail -5",
]


async def main():
    async with aiohttp.ClientSession() as s:
        token = (await (await s.get(f"{BASE}/token")).json())["token"]
        async with s.ws_connect(f"{BASE.replace('http', 'ws')}/ws/serial?token={token}") as ws:
            for cmd in CMDS:
                await ws.send_str(cmd + "\r")
                await asyncio.sleep(5)
            buf = []
            deadline = asyncio.get_event_loop().time() + 12
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await ws.receive(timeout=2)
                except asyncio.TimeoutError:
                    break
                if msg.type == aiohttp.WSMsgType.BINARY:
                    buf.append(msg.data.decode(errors="replace"))
            print("".join(buf)[-2500:])


asyncio.run(main())
