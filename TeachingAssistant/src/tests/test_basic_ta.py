# test_basic_ta.py
import asyncio
import pytest
from unittest.mock import AsyncMock
from TeachingAssistant.src.teaching_assistant.basic_ta import BasicTeachingAssistant

@pytest.mark.asyncio
async def test_start_and_end_session_sends_greeting_and_closing():
    ws = AsyncMock()
    ws.send_message = AsyncMock()
    # small monitor interval so tests run fast
    ta = BasicTeachingAssistant(ws, monitor_interval=0.02, checkin_throttle_seconds=0.005)

    await ta.start_session("Tester")
    # give a tiny moment for send_message to be awaited
    await asyncio.sleep(0.01)

    # greeting should have been sent at least once
    assert ws.send_message.await_count >= 1

    # simulate answering a question so monitor won't fire immediately
    ta.record_question_answered("q1", True)

    # end session should send closing prompt
    await ta.end_session("Tester")
    # after end_session, at least one more send_message call expected (closing)
    assert ws.send_message.await_count >= 2


@pytest.mark.asyncio
async def test_monitor_engagement_triggers_checkin():
    ws = AsyncMock()
    ws.send_message = AsyncMock()
    ta = BasicTeachingAssistant(ws, monitor_interval=0.03, checkin_throttle_seconds=0.005)

    await ta.start_session("Tester2")
    # do not record any question -> monitor should trigger a check-in
    await asyncio.sleep(0.05)  # allow monitor to run once

    # collect all sent messages
    called_texts = [call_args[0][0] for call_args in ws.send_message.call_args_list]

    # check at least one message contains phrasing from check-in prompt
    assert any("hasn't answered any questions" in t or "haven't answered any questions" in t or "check in" in t for t in called_texts)

    await ta.end_session("Tester2")

