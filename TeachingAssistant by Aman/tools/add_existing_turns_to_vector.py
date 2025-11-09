# tools/add_existing_turns_to_vector.py
import asyncio
from app.memory.session_store import get_recent
from app.memory.vector_store import vector_store

async def run():
    sess = "testsession"
    turns = await get_recent(sess, n=200)
    tutor_texts = [t["text"] for t in turns if t["speaker"] == "tutor"]
    print(f"Found {len(tutor_texts)} tutor turns to index.")
    for i, t in enumerate(tutor_texts):
        try:
            vector_store.add(t, {"session_id": sess, "idx": i, "type": "tutor_response"})
            print(f"Added {i+1}/{len(tutor_texts)}")
        except Exception as e:
            print("Vector store add failed:", e)
            break

    # IMPORTANT: persist the vector store metadata (and FAISS index if used)
    try:
        vector_store.save(path_dir="data")
        print("Vector store saved to data/")
    except Exception as e:
        print("Failed to save vector store:", e)

    print("Done indexing.")

if __name__ == "__main__":
    asyncio.run(run())
