# tools/test_memory.py
import asyncio
from app.memory.session_store import push_turn, get_recent

async def run():
    session = "demo123"
    await push_turn(session, "student", "What is photosynthesis?")
    await push_turn(session, "tutor", "It is how plants make food from sunlight.")
    rec = await get_recent(session)
    print(rec)

if __name__ == "__main__":
    asyncio.run(run())
