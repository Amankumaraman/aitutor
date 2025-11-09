# app/ws_stream.py
import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

load_dotenv()

from .ta.assistant import build_prompt, extract_quiz_and_answer
from .memory.session_store import push_turn, get_recent
from .memory.vector_store import vector_store

router = APIRouter()

GEMINI_STREAM_URL = os.getenv("GEMINI_STREAM_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# --- Development-only fake stream (keeps UI working without Gemini) ---
async def fake_stream(prompt):
    for chunk in [
        "This is the explanation. ",
        "Example: Apple falls due to gravity. ",
        "Mini-quiz: What force pulls objects toward Earth? [ANSWER: gravity]"
    ]:
        await asyncio.sleep(0.6)
        yield chunk
# --------------------------------------------------------------------


async def stream_from_gemini(prompt: str, params: dict):
    """
    Replace with real Gemini streaming call when available.
    For now this calls the fake_stream to let you demo locally.
    """
    # If you later implement real streaming, replace the body with httpx/ws code.
    async for c in fake_stream(prompt):
        yield c


@router.websocket("/ws/ta/{session_id}")
async def ta_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    stream_task = None
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "start_stream":
                user_prompt = msg.get("prompt", "")
                params = msg.get("params", {})

                # Build prompt (uses Redis recent + retrieval)
                composed_prompt = await build_prompt(session_id, user_prompt)

                # Save student message to session memory
                try:
                    await push_turn(session_id, "student", user_prompt)
                except Exception as e:
                    # don't block on Redis errors
                    print("Warning: push_turn failed:", e)

                # Stream in background
                response_text = ""
                async for token in stream_from_gemini(composed_prompt, params):
                    await websocket.send_text(json.dumps({"type": "partial", "chunk": token}))
                    response_text += token

                # Save tutor final message
                try:
                    await push_turn(session_id, "tutor", response_text)
                except Exception as e:
                    print("Warning: push_turn (tutor) failed:", e)

                # Persist into vector store (best-effort)
                try:
                    vector_store.add(response_text, {"session_id": session_id, "type": "tutor_response"})
                except Exception as e:
                    print("Vector store add failed:", e)

                # Notify client done
                await websocket.send_text(json.dumps({"type": "done"}))

                # Optionally send extracted quiz answer (hidden metadata to UI dev)
                ans = extract_quiz_and_answer(response_text)
                if ans:
                    await websocket.send_text(json.dumps({"type": "quiz_answer", "answer": ans}))

            elif mtype == "quiz_response":
                # student answered; grade against the most recent tutor answer that contains ANSWER:
                student_ans = msg.get("answer", "").strip().lower()
                recent = await get_recent(session_id, n=12)
                correct = None
                for turn in reversed(recent):
                    if turn.get("speaker") == "tutor" and "ANSWER:" in turn.get("text", ""):
                        try:
                            correct = turn["text"].split("ANSWER:")[-1].strip().strip("[] ").lower()
                        except Exception:
                            correct = None
                        break
                if correct is None:
                    await websocket.send_text(json.dumps({"type": "quiz_result", "score": 0, "feedback": "No stored answer found."}))
                else:
                    if student_ans == correct:
                        await websocket.send_text(json.dumps({"type": "quiz_result", "score": 1, "feedback": "Correct! 🎉"}))
                    elif student_ans in correct or correct in student_ans:
                        await websocket.send_text(json.dumps({"type": "quiz_result", "score": 0.8, "feedback": "Almost — small detail missing."}))
                    else:
                        await websocket.send_text(json.dumps({"type": "quiz_result", "score": 0, "feedback": f"Not quite. Hint: {correct}"}))

            elif mtype == "stop":
                if stream_task and not stream_task.done():
                    stream_task.cancel()
                await websocket.send_text(json.dumps({"type": "stopped"}))

            elif mtype == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                await websocket.send_text(json.dumps({"type": "unknown", "raw": msg}))

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        # Log and try to close cleanly
        print("WebSocket handler error:", e)
        try:
            await websocket.close()
        except Exception:
            pass
