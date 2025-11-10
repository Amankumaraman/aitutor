# TeachingAssistant/src/gemini_stream/websocket_client.py
import asyncio, json, os, time
from collections import deque
from typing import Dict, Any, Callable, List, Optional

try:
    import websockets
except Exception:
    websockets = None

class GeminiWebSocketClient:
    def __init__(self, api_key: Optional[str] = None, mock: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.websocket_url = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
        self.websocket = None
        self.is_connected = False
        self.conversation_buffer = deque(maxlen=5000)
        self.callbacks: List[Callable[[Dict[str, Any]], Any]] = []
        self._send_lock = asyncio.Lock()
        self._listen_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._mock = mock or os.getenv("GEMINI_MOCK", "false").lower() in ("1","true","yes")

    async def connect(self):
        if self._mock:
            self.is_connected = True
            print("[GeminiMock] connected (mock mode)")
            if not self._listen_task or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._mock_listener())
            return

        if websockets is None:
            raise RuntimeError("websockets not installed.")

        headers = {"Content-Type":"application/json"}
        if self.api_key:
            headers["x-goog-api-key"] = self.api_key

        try:
            self.websocket = await websockets.connect(self.websocket_url, extra_headers=headers)
            self.is_connected = True
            print("Connected to Gemini Live WebSocket")
            self._listen_task = asyncio.create_task(self.listen_for_messages())
        except Exception as e:
            print(f"Connection error: {e}")
            self.is_connected = False
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self.reconnect())

    async def _mock_listener(self):
        # minimal mock that does nothing. Tests can use send_message to simulate events.
        while self.is_connected:
            await asyncio.sleep(10)

    async def listen_for_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_message(data)
        except Exception as e:
            print(f"listen_for_messages error: {e}")
            self.is_connected = False
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self.reconnect())

    async def process_message(self, data: Dict[str, Any]):
        timestamp = time.time()
        # ADAM = serverContent.modelTurn, student = clientContent.turns
        if "serverContent" in data:
            content = data["serverContent"]
            if "modelTurn" in content:
                text = self.extract_text(content["modelTurn"])
                utterance = {"speaker":"adam","text":text,"timestamp":timestamp,"raw_data":data}
                self.conversation_buffer.append(utterance)
                await self.notify_callbacks(utterance)
        elif "clientContent" in data:
            content = data["clientContent"]
            if "turns" in content and content["turns"]:
                text = self.extract_text(content["turns"][0])
                utterance = {"speaker":"student","text":text,"timestamp":timestamp,"raw_data":data}
                self.conversation_buffer.append(utterance)
                await self.notify_callbacks(utterance)

    def extract_text(self, turn_data: Dict[str, Any]) -> str:
        if not turn_data:
            return ""
        parts = turn_data.get("parts", [])
        texts = []
        for p in parts:
            if isinstance(p, dict) and "text" in p:
                texts.append(p["text"])
        return " ".join(texts).strip()

    async def send_message(self, text: str):
        if not self.is_connected:
            print("Not connected to WebSocket; send skipped.")
            return
        message = {"clientContent":{"turns":[{"role":"user","parts":[{"text":text}]}]}}
        payload = json.dumps(message)
        async with self._send_lock:
            try:
                if self._mock:
                    mock_utt = {"speaker":"assistant_instruction","text":text,"timestamp":time.time()}
                    self.conversation_buffer.append(mock_utt)
                    await self.notify_callbacks(mock_utt)
                    return
                await self.websocket.send(payload)
            except Exception as e:
                print(f"send_message error: {e}")
                if not self._reconnect_task or self._reconnect_task.done():
                    self._reconnect_task = asyncio.create_task(self.reconnect())

    async def reconnect(self, max_retries: int = 5):
        for attempt in range(max_retries):
            wait_time = min(30, 2 ** attempt)
            print(f"Reconnecting in {wait_time}s (attempt {attempt+1}/{max_retries})...")
            await asyncio.sleep(wait_time)
            try:
                await self.connect()
                if self.is_connected:
                    return
            except Exception as e:
                print(f"Reconnect attempt failed: {e}")
        print("Max reconnection attempts reached.")

    def register_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.callbacks.append(callback)

    async def notify_callbacks(self, utterance: Dict[str, Any]):
        for cb in list(self.callbacks):
            try:
                res = cb(utterance)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                print(f"Callback error: {e}")

    def get_conversation_history(self, minutes: int = 5) -> list:
        cutoff = time.time() - (minutes * 60)
        return [u for u in self.conversation_buffer if u["timestamp"] > cutoff]

    async def close(self):
        self.is_connected = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try: await self._listen_task
            except asyncio.CancelledError: pass
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try: await self._reconnect_task
            except asyncio.CancelledError: pass
        if not self._mock and self.websocket:
            await self.websocket.close()
