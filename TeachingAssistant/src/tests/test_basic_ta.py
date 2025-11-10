# TeachingAssistant/src/tests/test_basic_ta.py
import asyncio
import pytest
from unittest.mock import AsyncMock
from TeachingAssistant.src.teaching_assistant.basic_ta import BasicTeachingAssistant

@pytest.mark.asyncio
async def test_start_and_end_session_sends_greeting_and_closing():
    ws = AsyncMock()
    ws.send_message = AsyncMock()
    ws.register_callback = AsyncMock()
    ta = BasicTeachingAssistant(ws, monitor_interval=0.02, checkin_throttle_seconds=0.005)

    await ta.start_session("Tester")
    await asyncio.sleep(0.01)
    assert ws.send_message.await_count >= 1

    ta.record_question_answered("q1", True)
    await ta.end_session("Tester")
    assert ws.send_message.await_count >= 2

@pytest.mark.asyncio
async def test_monitor_engagement_triggers_checkin():
    ws = AsyncMock()
    ws.send_message = AsyncMock()
    ws.register_callback = AsyncMock()
    ta = BasicTeachingAssistant(ws, monitor_interval=0.03, checkin_throttle_seconds=0.005)

    await ta.start_session("Tester2")
    await asyncio.sleep(0.06)
    called_texts = [call_args[0][0] for call_args in ws.send_message.call_args_list]
    assert any("hasn't answered any questions" in t or "check in" in t for t in called_texts)
    await ta.end_session("Tester2")
