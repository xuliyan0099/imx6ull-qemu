import asyncio, re
import aiohttp

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.get("http://127.0.0.1:8767/token") as r:
            token = (await r.json())["token"]
        async with s.ws_connect(f"ws://127.0.0.1:8767/ws/serial?token={token}") as ws:
            await ws.send_str("ping -c 2 8.8.8.8\r")
            await asyncio.sleep(4)
            buf = []
            deadline = asyncio.get_event_loop().time() + 8
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await ws.receive(timeout=2)
                except asyncio.TimeoutError:
                    break
                if msg.type == aiohttp.WSMsgType.BINARY:
                    buf.append(msg.data.decode(errors="replace"))
            text = "".join(buf)
            print("\n".join(l for l in text.splitlines() if re.search(r"PING|bytes from|packet loss|8\.8", l)))

asyncio.run(main())
