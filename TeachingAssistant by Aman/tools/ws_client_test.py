# tools/ws_client_test.py
import asyncio
import websockets
import json

async def main():
    uri = "ws://localhost:8000/ws/ta/testsession"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "start_stream", "prompt": "Explain gravity in simple terms"}))
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(">>", data)
            if data.get("type") == "done":
                break

if __name__ == "__main__":
    asyncio.run(main())
