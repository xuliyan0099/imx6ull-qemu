import asyncio, json, os, re
import aiohttp

BASE = os.environ.get("IM6_TEST_BASE", "http://127.0.0.1:8767")

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get(BASE + "/token") as r:
            token = (await r.json())["token"]
        async with s.ws_connect(f"{BASE.replace('http','ws')}/ws/serial?token={token}") as ws:
            async def send(cmd):
                await ws.send_str(cmd + "\r")
                await asyncio.sleep(2.5)
            for cmd in ["ifconfig eth0", "ifconfig eth1", "ping -c 2 10.0.2.2", "cat /proc/net/dev"]:
                await send(cmd)
            buf = []
            deadline = asyncio.get_event_loop().time() + 15
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await ws.receive(timeout=2)
                except asyncio.TimeoutError:
                    break
                if msg.type == aiohttp.WSMsgType.BINARY:
                    buf.append(msg.data.decode(errors="replace"))
                elif msg.type == aiohttp.WSMsgType.TEXT:
                    buf.append(msg.data)
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                    break
            text = "".join(buf)
            for line in text.splitlines():
                if re.search(r"eth0|10\.0\.2|bytes|packets|ping|PING", line):
                    print(line)

asyncio.run(main())
