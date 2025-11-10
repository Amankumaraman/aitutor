# basic_ta.py
import asyncio
import time
import json
from typing import Optional

class BasicTeachingAssistant:
    def __init__(self, websocket_client, monitor_interval: float = 60.0, checkin_throttle_seconds: float = 30.0):
        """
        websocket_client: instance with async send_message(text) and register_callback(cb)
        monitor_interval: how often (seconds) to check engagement
        checkin_throttle_seconds: minimum seconds between check-in prompts
        """
        self.websocket_client = websocket_client
        self.session_start_time: Optional[float] = None
        self.questions_log = []  # each entry: {'question_id', 'timestamp', 'is_correct', ...}
        self.is_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._background_tasks = []
        self.monitor_interval = monitor_interval
        self._last_checkin_time: Optional[float] = None
        self._checkin_throttle_seconds = checkin_throttle_seconds

    async def start_session(self, student_name: str):
        self.session_start_time = time.time()
        self.is_active = True
        greeting_prompt = f"""[SYSTEM PROMPT FOR ADAM]
You are starting a tutoring session with {student_name}.
Please greet them warmly and ask how they're doing today. Keep it short and encouraging."""
        await self.websocket_client.send_message(greeting_prompt)
        print(f"✓ Session started with greeting for {student_name}")

        # Start monitor task (store to cancel later)
        self._monitor_task = asyncio.create_task(self.monitor_engagement())
        self._background_tasks.append(self._monitor_task)

    async def end_session(self, student_name: str):
        self.is_active = False
        session_duration = (time.time() - (self.session_start_time or time.time())) / 60.0
        total_questions = len(self.questions_log)
        closing_prompt = f"""[SYSTEM PROMPT FOR ADAM]
The tutoring session is ending now.
Session stats: {session_duration:.1f} minutes, {total_questions} questions attempted.
Please give {student_name} a warm closing message and one actionable tip for next time."""
        await self.websocket_client.send_message(closing_prompt)
        print(f"✓ Session ended with closing greeting for {student_name}")

        # Cancel background tasks
        for t in list(self._background_tasks):
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        self._background_tasks.clear()

    def record_question_answered(self, question_id: str, is_correct: bool):
        entry = {'question_id': question_id, 'timestamp': time.time(), 'is_correct': is_correct}
        self.questions_log.append(entry)
        print(f"✓ Question recorded: {question_id} ({'correct' if is_correct else 'incorrect'})")

    def get_questions_in_last_60_seconds(self) -> int:
        cutoff = time.time() - 60.0
        return len([q for q in self.questions_log if q['timestamp'] > cutoff])

    async def monitor_engagement(self):
        try:
            while self.is_active:
                await asyncio.sleep(self.monitor_interval)
                if not self.is_active:
                    break

                questions_count = self.get_questions_in_last_60_seconds()
                if questions_count == 0:
                    now = time.time()
                    if self._last_checkin_time and (now - self._last_checkin_time) < self._checkin_throttle_seconds:
                        # skip to avoid spamming
                        continue
                    check_in_prompt = """[SYSTEM PROMPT FOR ADAM]
The student hasn't answered any questions in the last 60 seconds.
Please check in with them in a friendly, non-judgmental way: "Hey — are you still there? Need a hint or a break?"
Keep it casual and supportive."""
                    await self.websocket_client.send_message(check_in_prompt)
                    self._last_checkin_time = now
                    print("⚠ No activity in 60 seconds - sent check-in prompt")
        except asyncio.CancelledError:
            # expected on shutdown
            pass
        except Exception as e:
            print(f"monitor_engagement error: {e}")
