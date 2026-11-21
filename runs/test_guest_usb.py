import asyncio, os, re
import aiohttp

BASE = os.environ.get("IM6_TEST_BASE", "http://127.0.0.1:8767")

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{BASE}/token") as r:
            token = (await r.json())["token"]
        async with s.ws_connect(f"{BASE.replace('http','ws')}/ws/serial?token={token}") as ws:
            for cmd in ["lsusb", "dmesg | grep -i usb | tail -20"]:
                await ws.send_str(cmd + "\r")
                await asyncio.sleep(3)
            buf = []
            deadline = asyncio.get_event_loop().time() + 10
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await ws.receive(timeout=2)
                except asyncio.TimeoutError:
                    break
                if msg.type == aiohttp.WSMsgType.BINARY:
                    buf.append(msg.data.decode(errors="replace"))
            text = "".join(buf)
            print("\n".join(l for l in text.splitlines() if re.search(r"usb|USB|QEMU|audio|Audio|Bus", l)))

asyncio.run(main())
