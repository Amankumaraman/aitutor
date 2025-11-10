# TeachingAssistant/src/teaching_assistant/_demo.py
import asyncio
from TeachingAssistant.src.gemini_stream.websocket_client import GeminiWebSocketClient
from TeachingAssistant.src.teaching_assistant.basic_ta import BasicTeachingAssistant
from TeachingAssistant.src.memory.vector_store_adapter import VectorStoreAdapter
from TeachingAssistant.src.memory.knowledge_graph_adapter import KnowledgeGraphAdapter

async def main():
    client = GeminiWebSocketClient(mock=True)
    await client.connect()

    vector_store = VectorStoreAdapter(use_chroma=False)
    kg = KnowledgeGraphAdapter()

    # monitor_interval short for demo; set to 60 for real condition
    ta = BasicTeachingAssistant(client, vector_store=vector_store, knowledge_graph=kg, monitor_interval=3, checkin_throttle_seconds=1)

    await ta.start_session("DemoStudent")
    await asyncio.sleep(1)
    ta.record_question_answered("q1", True)
    await asyncio.sleep(1)
    ta.record_question_answered("q2", False)
    # wait long enough to trigger check-in (monitor_interval=3)
    await asyncio.sleep(5)

    print("Vector DB search for 'question':", vector_store.search_similar("question", limit=3))
    print("KG flow:", kg.get_conversation_flow())

    await ta.end_session("DemoStudent")
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
