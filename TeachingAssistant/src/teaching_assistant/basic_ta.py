# TeachingAssistant/src/teaching_assistant/basic_ta.py
import asyncio, time
from typing import Optional

class BasicTeachingAssistant:
    def __init__(self, websocket_client, vector_store=None, knowledge_graph=None, monitor_interval: float = 60.0, checkin_throttle_seconds: float = 30.0):
        self.websocket_client = websocket_client
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.session_start_time = None
        self.questions_log = []
        self.is_active = False
        self._monitor_task = None
        self._background_tasks = []
        self.monitor_interval = monitor_interval
        self._last_checkin_time = None
        self._checkin_throttle_seconds = checkin_throttle_seconds
        try:
            self.websocket_client.register_callback(self._on_new_utterance)
        except Exception:
            pass

    async def _on_new_utterance(self, utt):
        if self.vector_store:
            doc = {'id': f"utt_{utt.get('timestamp')}", 'text': utt.get('text',''), 'metadata': {'speaker': utt.get('speaker')}}
            self.vector_store.add_documents([doc])
        if self.knowledge_graph:
            nid = f"utt_{utt.get('timestamp')}"
            self.knowledge_graph.add_utterance_node(nid, utt.get('text',''), {'speaker':utt.get('speaker')})

    async def start_session(self, student_name: str):
        self.session_start_time = time.time()
        self.is_active = True
        greeting_prompt = f"""[SYSTEM PROMPT FOR ADAM]
You are starting a tutoring session with {student_name}.
Please greet them warmly and ask how they're doing today. Make them feel welcome and excited to learn."""
        await self.websocket_client.send_message(greeting_prompt)
        print(f"✓ Session started with greeting for {student_name}")
        self._monitor_task = asyncio.create_task(self.monitor_engagement())
        self._background_tasks.append(self._monitor_task)

    async def end_session(self, student_name: str):
        self.is_active = False
        session_duration = (time.time() - (self.session_start_time or time.time())) / 60.0
        total_questions = len(self.questions_log)
        closing_prompt = f"""[SYSTEM PROMPT FOR ADAM]
The tutoring session is ending now.
Session stats: {session_duration:.1f} minutes, {total_questions} questions attempted.
Please give {student_name} a warm closing message, acknowledge their hard work, and encourage them for next session."""
        await self.websocket_client.send_message(closing_prompt)
        print(f"✓ Session ended with closing greeting for {student_name}")
        for t in list(self._background_tasks):
            t.cancel()
            try: await t
            except asyncio.CancelledError: pass
        self._background_tasks.clear()

    def record_question_answered(self, question_id: str, is_correct: bool, difficulty: str = "medium", response_time: float = 30.0):
        self.questions_log.append({'question_id': question_id, 'timestamp': time.time(), 'is_correct': is_correct, 'difficulty': difficulty, 'response_time': response_time})
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
                        continue
                    check_in_prompt = """[SYSTEM PROMPT FOR ADAM]
The student hasn't answered any questions in the last 60 seconds.
Please check in with them in a friendly, non-judgmental way: "Hey, are you still there? Need a hint or a break?"
Keep it casual and supportive."""
                    await self.websocket_client.send_message(check_in_prompt)
                    self._last_checkin_time = now
                    print("⚠ No activity in 60 seconds - sent check-in prompt")
        except asyncio.CancelledError:
            pass
