# _demo.py
import asyncio
from TeachingAssistant.src.gemini_stream.websocket_client import GeminiWebSocketClient
from TeachingAssistant.src.teaching_assistant.basic_ta import BasicTeachingAssistant

async def main():
    client = GeminiWebSocketClient(mock=True)
    await client.connect()
    ta = BasicTeachingAssistant(client, monitor_interval=5)  # 5s for demo
    await ta.start_session("DemoStudent")
    await asyncio.sleep(2)
    ta.record_question_answered("demo_q1", True)
    await asyncio.sleep(7)  # allow check-in if needed
    await ta.end_session("DemoStudent")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
