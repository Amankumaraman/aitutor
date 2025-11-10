# websocket_client.py
import asyncio
import json
import time
import os
from collections import deque
from typing import Dict, Any, Callable, List, Optional

try:
    import websockets
except Exception:
    websockets = None  # websockets not available in test/mock env

class GeminiWebSocketClient:
    def __init__(self, api_key: str = None, mock: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.websocket_url = (
            "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
        )
        self.websocket = None
        self.is_connected = False
        self.conversation_buffer = deque(maxlen=5000)
        self.callbacks: List[Callable[[Dict[str, Any]], Any]] = []
        self._send_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._mock = mock or os.getenv("GEMINI_MOCK", "false").lower() in ("1", "true", "yes")

    async def connect(self):
        if self._mock:
            self.is_connected = True
            print("[GeminiMock] connected (mock mode)")
            # In mock mode, spawn a simple loop that sends fake messages for testing if needed
            self._listen_task = asyncio.create_task(self._mock_listener())
            return

        if websockets is None:
            raise RuntimeError("websockets library not available and not running in mock mode.")

        headers = {"Content-Type": "application/json"}
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
            # start reconnect attempts
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self.reconnect())

    async def _mock_listener(self):
        """Emit no-op or occasional sample utterances for local dev."""
        while self.is_connected:
            await asyncio.sleep(10)
            # no-op by default; tests can call notify_callbacks directly

    async def listen_for_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_message(data)
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.is_connected = False
            await self.reconnect()

    async def process_message(self, data: Dict[str, Any]):
        timestamp = time.time()

        # serverContent = ADAM; clientContent = student (from provided pseudo)
        if "serverContent" in data:
            content = data["serverContent"]
            if "modelTurn" in content:
                text = self.extract_text(content["modelTurn"])
                utterance = {"speaker": "adam", "text": text, "timestamp": timestamp, "raw_data": data}
                self.conversation_buffer.append(utterance)
                await self.notify_callbacks(utterance)

        elif "clientContent" in data:
            content = data["clientContent"]
            if "turns" in content and content["turns"]:
                text = self.extract_text(content["turns"][0])
                utterance = {"speaker": "student", "text": text, "timestamp": timestamp, "raw_data": data}
                self.conversation_buffer.append(utterance)
                await self.notify_callbacks(utterance)

    def extract_text(self, turn_data: Dict[str, Any]) -> str:
        if not turn_data:
            return ""
        parts = turn_data.get("parts") or []
        texts = []
        for p in parts:
            if isinstance(p, dict) and "text" in p:
                texts.append(p["text"])
        return " ".join(texts).strip()

    async def send_message(self, text: str):
        """Send system/client message to Gemini. Serialized via lock to avoid concurrent writes."""
        if not self.is_connected:
            print("Not connected to WebSocket; cannot send.")
            return

        message = {"clientContent": {"turns": [{"role": "user", "parts": [{"text": text}]}]}}
        payload = json.dumps(message)

        async with self._send_lock:
            try:
                if self._mock:
                    # In mock mode, also append to buffer as ADAM would receive it
                    mock_utterance = {"speaker": "assistant_instruction", "text": text, "timestamp": time.time()}
                    self.conversation_buffer.append(mock_utterance)
                    # optionally notify callbacks so TA tests observe this
                    await self.notify_callbacks(mock_utterance)
                    return

                await self.websocket.send(payload)
            except Exception as e:
                print(f"Send error: {e}")
                # attempt a reconnect and retry once
                await self.reconnect()
                try:
                    if self.websocket:
                        await self.websocket.send(payload)
                except Exception as e2:
                    print(f"Retry send failed: {e2}")

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
        print("Max reconnection attempts reached, giving up for now.")

    def register_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        self.callbacks.append(callback)

    async def notify_callbacks(self, utterance: Dict[str, Any]):
        for cb in list(self.callbacks):
            try:
                result = cb(utterance)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"Callback error: {e}")

    def get_conversation_history(self, minutes: int = 5) -> list:
        cutoff = time.time() - (minutes * 60)
        return [u for u in self.conversation_buffer if u["timestamp"] > cutoff]

    async def close(self):
        self.is_connected = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        if not self._mock and self.websocket:
            await self.websocket.close()
