# bulk_simulate.py
import asyncio, time
from TeachingAssistant.src.gemini_stream.websocket_client import GeminiWebSocketClient
from TeachingAssistant.src.memory.vector_store_adapter import VectorStoreAdapter
from TeachingAssistant.src.memory.knowledge_graph_adapter import KnowledgeGraphAdapter

async def main():
    client = GeminiWebSocketClient(mock=True)
    await client.connect()
    vs = VectorStoreAdapter(use_chroma=False)
    kg = KnowledgeGraphAdapter()
    for i in range(60):
        utt = {"speaker":"student","text":f"sample utterance {i}","timestamp":time.time()}
        client.conversation_buffer.append(utt)
        doc = {'id': f"utt_{i}", 'text': utt['text'], 'metadata': {'speaker':'student'}}
        vs.add_documents([doc])
        kg.add_utterance_node(f"utt_{i}", utt['text'], {'speaker':'student'})
        await asyncio.sleep(0.01)
    print("Stored utterances:", len(vs._docs) if not vs.use_chroma else "chroma")
    print("KG nodes:", len(kg.g.nodes()))
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
