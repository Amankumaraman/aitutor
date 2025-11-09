# app/ta/assistant.py
from ..memory.session_store import get_recent
from ..memory.vector_store import vector_store

SYSTEM_PROMPT = """
You are a friendly AI teaching assistant.
Rules:
- Explain clearly and simply with examples.
- Provide one 1-question mini-quiz after your explanation.
- Include the teacher answer as [ANSWER: ...] (this may be extracted and used for grading).
- If the student's message is unclear, ask one clarifying question.
- Keep answers under 200 words.
"""

async def build_prompt(session_id: str, user_input: str):
    recent = await get_recent(session_id, n=8)
    history = "\n".join([f"{m['speaker']}: {m['text']}" for m in recent])
    retrieved = vector_store.search(user_input, k=3)
    context = "\n".join([r.get("text", "") for r in retrieved])
    prompt = f"{SYSTEM_PROMPT}\nContext:\n{context}\n\nRecent:\n{history}\n\nStudent: {user_input}\nTutor:"
    return prompt

def extract_quiz_and_answer(llm_text: str):
    # look for "ANSWER:" in the last few lines
    lines = llm_text.strip().splitlines()
    for line in reversed(lines[-6:]):
        if "ANSWER:" in line:
            return line.split("ANSWER:")[-1].strip("[] ").strip()
    return None
