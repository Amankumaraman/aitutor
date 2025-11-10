# TeachingAssistant/src/conversation/transcription.py
import asyncio, time, os
from collections import deque

try:
    import speech_recognition as sr
except Exception:
    sr = None

class ConversationTranscriber:
    def __init__(self, language='en-US', mock: bool = False):
        self.recognizer = sr.Recognizer() if sr else None
        self.language = language
        self.is_listening = False
        self.student_transcript = deque(maxlen=1000)
        self.adam_transcript = deque(maxlen=1000)
        self.mock = mock or os.getenv("TRANSCRIBER_MOCK","true").lower() in ("1","true","yes")

    async def start_continuous_listening(self, on_utterance=None):
        self.is_listening = True
        while self.is_listening:
            if self.mock:
                await asyncio.sleep(1)
                continue
            else:
                with self.recognizer.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                text = await asyncio.get_event_loop().run_in_executor(None, lambda: self.recognizer.recognize_google(audio, language=self.language))
                ts = time.time()
                utt = {'speaker':'student','text':text,'timestamp':ts}
                self.student_transcript.append(utt)
                if on_utterance:
                    await on_utterance(utt)

    def record_adam_response(self, text: str):
        self.adam_transcript.append({'speaker':'adam','text':text,'timestamp':time.time()})
