# tools/ws_quiz_reply.py
import asyncio
import websockets
import json

async def run():
    uri = "ws://localhost:8000/ws/ta/testsession"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "start_stream", "prompt": "Explain gravity simply and include a mini-quiz."}))
        correct_answer = None
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print("RECV:", data)
            if data.get("type") == "quiz_answer":
                correct_answer = data.get("answer")
                # we print it so you can see what the server extracted (useful during testing)
                print("Server says quiz answer (hidden):", correct_answer)
            if data.get("type") == "done":
                break

        # Ask user for input to reply, but default to correct answer if Enter pressed
        student_reply = input("Type your quiz answer to send (press Enter to send the correct answer): ").strip()
        if not student_reply and correct_answer:
            student_reply = correct_answer
            print("(Using the correct answer)")

        await ws.send(json.dumps({"type": "quiz_response", "answer": student_reply}))
        # wait for server grading
        msg = await ws.recv()
        print("Response from server:", msg)

if __name__ == "__main__":
    asyncio.run(run())
