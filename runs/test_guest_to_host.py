import asyncio, os
import aiohttp

BASE = os.environ.get("IM6_TEST_BASE", "http://127.0.0.1:8765")
CMDS = [
    "busybox wget -T 5 -O /tmp/host.txt http://10.0.2.2:8000/net-test.txt; cat /tmp/host.txt",
]


async def main():
    async with aiohttp.ClientSession() as s:
        token = (await (await s.get(f"{BASE}/token")).json())["token"]
        async with s.ws_connect(f"{BASE.replace('http', 'ws')}/ws/serial?token={token}") as ws:
            for cmd in CMDS:
                await ws.send_str(cmd + "\r")
                await asyncio.sleep(6)
            buf = []
            deadline = asyncio.get_event_loop().time() + 8
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await ws.receive(timeout=2)
                except asyncio.TimeoutError:
                    break
                if msg.type == aiohttp.WSMsgType.BINARY:
                    buf.append(msg.data.decode(errors="replace"))
            print("".join(buf)[-1800:])


asyncio.run(main())
