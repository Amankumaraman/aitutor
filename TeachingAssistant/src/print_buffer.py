# print_buffer.py
import asyncio
from TeachingAssistant.src.gemini_stream.websocket_client import GeminiWebSocketClient

async def main():
    c = GeminiWebSocketClient(mock=True)
    await c.connect()
    await c.send_message("hello from test")
    await asyncio.sleep(0.1)
    items = list(c.conversation_buffer)[-10:]
    print("Last buffer items:")
    for it in items:
        print(it)
    await c.close()

if __name__ == "__main__":
    asyncio.run(main())
